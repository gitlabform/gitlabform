import json
import logging

import cli_ui
import requests
import os

import urllib3
from urllib3.util.retry import Retry
from urllib import parse
from requests.adapters import HTTPAdapter

from gitlabform.configuration import Configuration


class GitLabCore:
    def __init__(self, config_path=None, config_string=None):

        self.configuration = Configuration(config_path, config_string)

        self.url = self.configuration.get("gitlab|url", os.getenv("GITLAB_URL"))
        self.token = self.configuration.get("gitlab|token", os.getenv("GITLAB_TOKEN"))
        self.ssl_verify = self.configuration.get("gitlab|ssl_verify", True)
        self.timeout = self.configuration.get("gitlab|timeout", 10)

        self.session = requests.Session()

        retries = Retry(
            total=3, backoff_factor=0.25, status_forcelist=[500, 502, 503, 504]
        )

        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))

        self.session.verify = self.ssl_verify
        if not self.ssl_verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        try:
            version = self._make_requests_to_api("version")
            cli_ui.debug(
                f"Connected to GitLab version: {version['version']} ({version['revision']})"
            )
        except Exception as e:
            raise TestRequestFailedException(e)

    def get_configuration(self):
        return self.configuration

    def get_project(self, project_and_group_or_id):
        return self._make_requests_to_api("projects/%s", project_and_group_or_id)

    def _get_user_id(self, username):
        users = self._make_requests_to_api("users?username=%s", username, "GET")

        # this API endpoint is for lookup, not search, so 'username' has to be full and exact username
        # also it's not possible to get more than 1 user as a result

        if len(users) == 0:
            raise NotFoundException(
                "No users found when searching for username '%s'" % username
            )

        return users[0]["id"]

    def _get_user(self, user_id):
        return self._make_requests_to_api("users/%s", str(user_id), "GET")

    def _get_group_id(self, path):
        group = self._make_requests_to_api("groups/%s", path, "GET")
        # TODO: add tests for all that uses this and then stop converting these ints to strings here
        return str(group["id"])

    def _get_project_id(self, project_and_group):
        # This is a NEW workaround for https://github.com/gitlabhq/gitlabhq/issues/8290
        result = self.get_project(project_and_group)
        return str(result["id"])

    def _make_requests_to_api(
        self,
        path_as_format_string,
        args=None,
        method="GET",
        data=None,
        expected_codes=200,
        paginated=False,
        json=None,
    ):
        """
        Makes a HTTP request (or requests) to the GitLab API endpoint. It takes case of making as many requests as
        needed in case we are using a paginated endpoint. (See underlying method for authentication, retries,
        timeout etc.)

        :param path_as_format_string: path with parts to be replaced by values from `args` replaced by '%s'
                                      (aka the old-style Python string formatting, see:
                                       https://docs.python.org/2/library/stdtypes.html#string-formatting )
        :param args: single element or a tuple of values to put under '%s's in `path_as_format_string`
        :param method: uppercase string of a HTTP method name, like 'GET' or 'PUT'
        :param data: dict with data to be 'PUT'ted or 'POST'ed
        :param expected_codes: a single HTTP code (like: 200) or a list of accepted HTTP codes
                               - if the call to the API will return other code an exception will be thrown
        :param paginated: if given API is paginated (see https://docs.gitlab.com/ee/api/#pagination )
        :param json: alternatively to `dict` you can set this to a string that can be parsed as JSON that will
                     be used as data to be 'PUT'ted or 'POST'ed
        :return: data returned by the endpoint, as a JSON object. If the API is paginated the it returns JSONs with
                 arrays of objects and then this method returns JSON with a single array that contains all of those
                 objects.
        """
        if not paginated:
            response = self._make_request_to_api(
                path_as_format_string, args, method, data, expected_codes, json
            )
            return response.json()
        else:
            if "?" in path_as_format_string:
                path_as_format_string += "&per_page=100"
            else:
                path_as_format_string += "?per_page=100"

            first_response = self._make_request_to_api(
                path_as_format_string, args, method, data, expected_codes, json
            )
            results = first_response.json()

            # In newer versions of GitLab the 'X-Total-Pages' may not be available
            # anymore, see https://gitlab.com/gitlab-org/gitlab/-/merge_requests/43159
            # so let's switch to thew newer style.

            response = first_response
            while True:
                if "x-next-page" in response.headers:
                    next_page = response.headers["x-next-page"]
                    response = self._make_request_to_api(
                        path_as_format_string + "&page=" + str(next_page),
                        args,
                        method,
                        data,
                        expected_codes,
                        json,
                    )
                    results += response.json()
                else:
                    break

        return results

    def _make_request_to_api(
        self, path_as_format_string, args, method, dict_data, expected_codes, json_data
    ):

        """
        Makes a single request to the GitLab API. Takes care of the authentication, basic error processing,
        retries, timeout etc.

        :param for the params description please see `_make_requests_to_api()`
        :return: data returned by the endpoint, as a JSON object.
        """

        expected_codes = self._listify(expected_codes)

        if dict_data and json_data:
            raise Exception(
                "You need to pass the either as dict (dict_data) or JSON (json_data), not both!"
            )

        url = (
            self.url
            + "/api/v4/"
            + self._format_with_url_encoding(path_as_format_string, args)
        )
        logging.debug(
            "url = %s , method = %s , data = %s, json = %s",
            url,
            method,
            json.dumps(dict_data, sort_keys=True),
            json.dumps(json_data, sort_keys=True),
        )
        headers = {
            "PRIVATE-TOKEN": self.token,
            "Authorization": "Bearer " + self.token,
        }
        if dict_data:
            response = self.session.request(
                method, url, headers=headers, data=dict_data, timeout=self.timeout
            )
        elif json_data:
            response = self.session.request(
                method, url, headers=headers, json=json_data, timeout=self.timeout
            )
        else:
            response = self.session.request(
                method, url, headers=headers, timeout=self.timeout
            )
        logging.debug("response code=%s" % response.status_code)

        if response.status_code == 204:
            # code calling this function assumes that it can do response.json() so fake it to return empty dict
            response.json = lambda: {}

        if response.status_code not in expected_codes:
            if response.status_code == 404:
                raise NotFoundException("Resource path='%s' not found!" % url)
            else:
                raise UnexpectedResponseException(
                    "Request url='%s', method=%s, data='%s' failed - expected code(s) %s, got code %s & body: '%s'"
                    % (
                        url,
                        method,
                        dict_data,
                        str(expected_codes),
                        response.status_code,
                        response.content,
                    ),
                    response.status_code,
                )

        logging.debug("response json=%s" % json.dumps(response.json(), sort_keys=True))
        return response

    @staticmethod
    def _format_with_url_encoding(format_string, single_arg_or_args_tuple):

        # we want to URL-encode all the args, but not the path itself which looks like "/foo/%s/bar"
        # because '/'s here are NOT to be URL-encoded

        if not single_arg_or_args_tuple:
            # there are no params, so the format_string is the URL
            return format_string
        else:
            if type(single_arg_or_args_tuple) == tuple:
                # URL-encode each arg in the tuple and return it as tuple too
                url_encoded_args = ()
                for arg in single_arg_or_args_tuple:
                    url_encoded_args += (parse.quote_plus(str(arg)),)
            else:
                # URL-encode single arg
                url_encoded_args = parse.quote_plus(single_arg_or_args_tuple)

            return format_string % url_encoded_args

    @staticmethod
    def _listify(expected_codes):
        if isinstance(expected_codes, int):
            return [expected_codes]
        else:
            return expected_codes


class TestRequestFailedException(Exception):
    pass


class ApiVersionIncorrectException(Exception):
    pass


class NotFoundException(Exception):
    pass


class TimeoutWaitingForDeletion(Exception):
    pass


class UnexpectedResponseException(Exception):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return self.message
