import json
import sys
import logging
import requests
import os
from urllib3.util.retry import Retry
from urllib import parse
from requests.adapters import HTTPAdapter

from gitlabform.configuration import Configuration
from gitlabform.configuration.core import KeyNotFoundException


class GitLabCore:

    url = None
    token = None
    ssl_verify = None
    session = None

    def __init__(self, config_path=None, config_string=None):

        if config_path and config_string:
            logging.fatal('Please initialize with either config_path or config_string, not both.')
            sys.exit(1)

        if config_path:
            configuration = Configuration(config_path=config_path)
        else:
            configuration = Configuration(config_string=config_string)

        self.url = configuration.get("gitlab|url", os.getenv("GITLAB_URL"))
        self.token = configuration.get("gitlab|token", os.getenv("GITLAB_TOKEN"))
        self.ssl_verify = configuration.get("gitlab|ssl_verify", True)

        self.session = requests.Session()

        retries = Retry(total=3,
                        backoff_factor=0.25,
                        status_forcelist=[500, 502, 503, 504])

        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.verify = self.ssl_verify

        try:
            version = self._make_requests_to_api("version")
            logging.info("Connected to GitLab version: %s (%s)" % (version['version'], version['revision']))
        except Exception as e:
            raise TestRequestFailedException(e)
        try:
            api_version = configuration.get("gitlab|api_version")
            if api_version != 4:
                raise ApiVersionIncorrectException()
        except KeyNotFoundException:
            logging.fatal("Aborting. GitLabForm 1.0.0 has switched from GitLab API v3 to v4 in which some parameter "
                          "names have changed. By its design GitLabForm reads some parameter names directly from "
                          "config.yml so you need to update those names by yourself. See changes in config.yml "
                          "in this diff to see what had to be changed there: "
                          "https://github.com/egnyte/gitlabform/pull/28/files . "
                          "After updating your config.yml please add 'api_version' key to 'gitlab' section and set it "
                          "to 4 to indicate that your config is v4-compatible.")
            sys.exit(3)

    def get_project(self, project_and_group_or_id):
        return self._make_requests_to_api("projects/%s", project_and_group_or_id)

    def _get_user_id(self, username):
        users = self._make_requests_to_api("users?username=%s", username, 'GET')

        # this API endpoint is for lookup, not search, so 'username' has to be full and exact username
        # also it's not possible to get more than 1 user as a result

        if len(users) == 0:
            raise NotFoundException("No users found when searching for username '%s'" % username)

        return users[0]['id']

    def _get_user(self, user_id):
        return self._make_requests_to_api("users/%s", str(user_id), 'GET')

    def _get_group_id(self, path):
        group = self._make_requests_to_api("groups/%s", path, 'GET')
        # TODO: add tests for all that uses this and then stop converting these ints to strings here
        return str(group['id'])

    def _get_project_id(self, project_and_group):
        # This is a NEW workaround for https://github.com/gitlabhq/gitlabhq/issues/8290
        result = self.get_project(project_and_group)
        return str(result['id'])

    def _make_requests_to_api(self, path_as_format_string, args=None, method='GET', data=None, expected_codes=200,
                              paginated=False, json=None):
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
            response = self._make_request_to_api(path_as_format_string, args, method, data, expected_codes, json)
            return response.json()
        else:
            if '?' in path_as_format_string:
                path_as_format_string += '&per_page=100'
            else:
                path_as_format_string += '?per_page=100'

            first_response = self._make_request_to_api(path_as_format_string, args, method, data, expected_codes, json)
            results = first_response.json()
            total_pages = int(first_response.headers['X-Total-Pages'])
            for page in range(2, total_pages + 1):
                response = self._make_request_to_api(path_as_format_string + "&page=" + str(page), args, method, data,
                                                     expected_codes, json)
                results += response.json()

        return results

    def _make_request_to_api(self, path_as_format_string, args, method, dict_data, expected_codes, json_data):

        """
        Makes a single request to the GitLab API. Takes care of the authentication, basic error processing,
        retries, timeout etc.

        :param for the params description please see `_make_requests_to_api()`
        :return: data returned by the endpoint, as a JSON object.
        """

        expected_codes = self._listify(expected_codes)

        if dict_data and json_data:
            raise Exception("You need to pass the either as dict (dict_data) or JSON (json_data), not both!")

        url = self.url + "/api/v4/" + self._format_with_url_encoding(path_as_format_string, args)
        logging.debug("url = %s , method = %s , data = %s, json = %s", url, method,
                      json.dumps(dict_data, sort_keys=True), json.dumps(json_data, sort_keys=True))
        headers = {
            'PRIVATE-TOKEN': self.token,
            'Authorization': 'Bearer ' + self.token,
        }
        if dict_data:
            response = self.session.request(method, url, headers=headers, data=dict_data, timeout=10)
        elif json_data:
            response = self.session.request(method, url, headers=headers, json=json_data, timeout=10)
        else:
            response = self.session.request(method, url, headers=headers, timeout=10)
        logging.debug("response code=%s" % response.status_code)

        if response.status_code == 204:
            # code calling this function assumes that it can do response.json() so fake it to return empty dict
            response.json = lambda: {}

        if response.status_code not in expected_codes:
            if response.status_code == 404:
                raise NotFoundException("Resource path='%s' not found!" % url)
            else:
                raise UnexpectedResponseException(
                    "Request url='%s', method=%s, data='%s' failed - expected code(s) %s, got code %s & body: '%s'" %
                    (url, method, dict_data, str(expected_codes), response.status_code, response.content),
                    response.status_code)

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
                    url_encoded_args += (parse.quote_plus(str(arg)), )
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


class UnexpectedResponseException(Exception):

    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return self.message
