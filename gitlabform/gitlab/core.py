import functools
import os
import re
from logging import debug
from urllib import parse

import httpx
import pkg_resources

# noinspection PyPackageRequirements
import urllib3
from cli_ui import debug as verbose

from gitlabform.configuration import Configuration
from gitlabform.ui import to_str


class GitLabCore:
    def __init__(self, config_path=None, config_string=None):

        self.configuration = Configuration(config_path, config_string)

        url = self.configuration.get("gitlab|url", os.getenv("GITLAB_URL"))
        # trim the redundant trailing slash(es)
        self.url = re.sub(r"/+$", "", url)
        self.token = self.configuration.get("gitlab|token", os.getenv("GITLAB_TOKEN"))
        self.ssl_verify = self.configuration.get("gitlab|ssl_verify", True)
        self.timeout = self.configuration.get("gitlab|timeout", 10)

        self.http_client = httpx.Client()

        # TODO: re-add retry using tenacity library

        self.http_client.verify = self.ssl_verify
        if not self.ssl_verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.http_client.timeout = self.timeout

        self.gitlabform_version = pkg_resources.get_distribution("gitlabform").version
        self.requests_version = pkg_resources.get_distribution("requests").version
        self.http_client.headers = {
            "private-token": self.token,
            "authorization": f"Bearer {self.token}",
            "user-agent": f"GitLabForm/{self.gitlabform_version} (python-requests/{self.requests_version})",
        }

        try:
            version = self._make_requests_to_api("version")
            verbose(
                f"Connected to GitLab version: {version['version']} ({version['revision']})"
            )
            self.version = version["version"]
        except Exception as e:
            raise TestRequestFailedException(e)

    def get_configuration(self):
        return self.configuration

    def get_project(self, project_and_group_or_id):
        return self._make_requests_to_api("projects/%s", project_and_group_or_id)

    @functools.lru_cache()
    def _get_user_id(self, username):
        users = self._make_requests_to_api("users?username=%s", username, "GET")

        # this API endpoint is for lookup, not search, so 'username' has to be full and exact username
        # also it's not possible to get more than 1 user as a result

        if len(users) == 0:
            raise NotFoundException(
                "No users found when searching for username '%s'" % username
            )

        return users[0]["id"]

    @functools.lru_cache()
    def _get_group_id(self, path):
        group = self._make_requests_to_api("groups/%s", path, "GET")
        # TODO: add tests for all that uses this and then stop converting these ints to strings here
        return str(group["id"])

    @functools.lru_cache()
    def _get_project_id(self, project_and_group):
        # This is a NEW workaround for https://github.com/gitlabhq/gitlabhq/issues/8290
        result = self.get_project(project_and_group)
        return str(result["id"])

    def has_no_license(self):
        license = self._make_requests_to_api("license")
        return not license or license["expired"]

    def _make_requests_to_api(
        self,
        path_as_format_string,
        args=None,
        method="GET",
        data=None,
        expected_codes=200,
        json=None,
    ):
        """
        Makes an HTTP request or requests to the GitLab API endpoint. More than one request is made automatically
        if the endpoint is paginated. (See underlying method for authentication, retries, timeout etc.)

        :param path_as_format_string: path with parts to be replaced by values from `args` replaced by '%s'
                                      (aka the old-style Python string formatting, see:
                                       https://docs.python.org/2/library/stdtypes.html#string-formatting )
        :param args: single element or a tuple of values to put under '%s's in `path_as_format_string`
        :param method: uppercase string of a HTTP method name, like 'GET' or 'PUT'
        :param data: dict with data to be 'PUT'ted or 'POST'ed
        :param expected_codes: a single HTTP code (like: 200) or a list of accepted HTTP codes
                               - if the call to the API will return other code an exception will be thrown
        :param json: alternatively to `dict` you can set this to a string that can be parsed as JSON that will
                     be used as data to be 'PUT'ted or 'POST'ed
        :return: data returned by the endpoint, as a JSON object. If the API is paginated, it returns JSONs with
                 arrays of objects and then this method returns JSON with a single array that contains all of those
                 objects.
        """
        if method != "GET":
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

            # In newer versions of GitLab the 'x-total-pages' may not be available
            # anymore, see https://gitlab.com/gitlab-org/gitlab/-/merge_requests/43159
            # so let's use the 'x-next-page' header instead

            response = first_response
            while True:
                if (
                    "x-next-page" in response.headers
                    and response.headers["x-next-page"]
                ):
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
                "You need to pass the data either as dict (dict_data) or JSON (json_data), not both!"
            )

        url = f"{self.url}/api/v4/{self._format_with_url_encoding(path_as_format_string, args)}"
        if dict_data:
            request = self.http_client.build_request(
                method,
                url,
                data=dict_data,
            )
            debug(f"===> data = {to_str(dict_data)}")
        elif json_data:
            request = self.http_client.build_request(
                method,
                url,
                json=json_data,
            )
            debug(f"===> json = {to_str(json_data)}")
        else:
            request = self.http_client.build_request(method, url)

        response = self.http_client.send(request)

        if response.status_code in expected_codes:
            # if we accept error responses then they will likely not contain a JSON body
            # so fake it to fix further calls to response.json()
            if response.status_code == 204 or (400 <= response.status_code <= 499):
                response.json = lambda: {}
        else:
            if response.status_code == 404:
                raise NotFoundException(
                    f"Resource with url='{url}' not found (HTTP 404)!"
                )
            else:
                if dict_data:
                    data_output = f"  data: {to_str(dict_data)}\n"
                elif json_data:
                    data_output = f"  json: {to_str(json_data)}\n"
                else:
                    data_output = ""

                try:
                    body = to_str(response.json())
                except:
                    body = response.text

                raise UnexpectedResponseException(
                    f"Unexpected response to request to GitLab API.\n"
                    f"Request:\n"
                    f"  url: {url}\n"
                    f"  method: {method}\n"
                    f"{data_output}"
                    f"  expected code(s): {str(expected_codes)}\n"
                    f"Response:\n"
                    f"  code: {response.status_code}\n"
                    f"  body: {body}\n",
                    response.status_code,
                    response.text,
                )
        if response.json():
            debug(f"<--- json = {to_str(response.json())}")
        else:
            debug(f"<--- json = (empty))")
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
                url_encoded_args = parse.quote_plus(str(single_arg_or_args_tuple))

            return format_string % url_encoded_args

    @staticmethod
    def _listify(expected_codes):
        if isinstance(expected_codes, int):
            return [expected_codes]
        else:
            return expected_codes


class TestRequestFailedException(Exception):
    def __init__(self, underlying: Exception):
        self.underlying = underlying


class NotFoundException(Exception):
    pass


class TimeoutWaitingForDeletion(Exception):
    pass


class InvalidParametersException(Exception):
    pass


class UnexpectedResponseException(Exception):
    def __init__(self, message: str, response_status_code: int, response_text: str):
        self.message: str = message
        self.response_status_code: int = response_status_code
        self.response_text: str = response_text

    def __str__(self):
        return self.message
