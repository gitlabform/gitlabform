import sys
import logging
import urllib
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from gitlabform.configuration.core import ConfigurationCore, KeyNotFoundException

s = requests.Session()

retries = Retry(total=3,
                backoff_factor=0.25,
                status_forcelist=[500, 502, 503, 504])

s.mount('http://', HTTPAdapter(max_retries=retries))
s.mount('https://', HTTPAdapter(max_retries=retries))


class GitLabCore:

    url = None
    __token = None

    def __init__(self, config_path=None):
        configuration = ConfigurationCore(config_path)
        self.url = configuration.get("gitlab|url")
        self.__token = configuration.get("gitlab|token")
        try:
            version = self._make_requests_to_api("version")
            logging.info("Connected to GitLab version: %s (%s)" % (version['version'], version['revision']))
        except Exception as e:
            raise TestRequestFailedException(e)
        try:
            api_version = configuration.get("gitlab|api_version")
            if api_version != 4:
                raise ApiVersionIncorrectException(e)
            logging.info("Config file is declared to be compatible with GitLab API v4")
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

    def _get_group_id(self, path):
        groups = self._make_requests_to_api("groups?search=%s", path, 'GET')

        # this API endpoint is for search, not lookup, so: 1. we may find more than 1 group if the 'group' is part of
        # more than 1 groups name or path, for example: search for 'foo' will return 'foo' and 'foobar' groups.
        # 2. we may find non-exact match, for example: search for 'foo' will return 'foobar' group.
        # we only want the exact matches here.

        if len(groups) == 0:
            raise NotFoundException("No groups found when searching for group path '%s'" % path)

        for group in groups:
            if group['path'] == path:
                return group['id']

        raise NotFoundException("None of the found group(s) when searching for group path '%s'"
                                " has an exactly matching path: %s" % (path, groups))

    def _get_project_id(self, project_and_group):
        # This is a NEW workaround for https://github.com/gitlabhq/gitlabhq/issues/8290
        result = self.get_project(project_and_group)
        return str(result['id'])

    def _make_requests_to_api(self, path_as_format_string, args=None, method='GET', data=None, expected_codes=200,
                              paginated=False, json=None):
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

    def _make_request_to_api(self, path_as_format_string, args, method, data, expected_codes, json):
        if data and json:
            raise Exception("You need to pass either data or json, not both!")

        url = self.url + "/api/v4/" + self._format_with_url_encoding(path_as_format_string, args)
        logging.debug("URL-encoded url=%s" % url)
        headers = {'PRIVATE-TOKEN': self.__token}
        if data:
            response = s.request(method, url, headers=headers, data=data, timeout=10)
        elif json:
            response = s.request(method, url, headers=headers, json=json, timeout=10)
        else:
            response = s.request(method, url, headers=headers, timeout=10)
        logging.debug("response code=%s" % response.status_code)
        if response.status_code == 404:
            raise NotFoundException("Resource path='%s' not found!" % url)
        elif response.status_code == 204:
            # code calling this function assumes that it can do response.json() so fake it to return empty dict
            response.json = lambda: {}
            return response
        elif not self._is_expected_code(response.status_code, expected_codes):
            e = UnexpectedResponseException(
                "Request url='%s', method=%s, data='%s' failed "
                "- expected code(s) %s, got code %s & body: '%s'" %
                (url, method, data,
                 self._expected_code_to_str(expected_codes), response.status_code, response.content))
            e.status_code = response.status_code
            raise e
        else:
            return response

    @staticmethod
    def _format_with_url_encoding(format_string, single_arg_or_args_tuple):

        # we want to URL-encode all the args, but not the path itself which looks like "/foo/%s/bar"
        # because / here are NOT to be URL-encoded

        if not single_arg_or_args_tuple:
            # there are no params, so the format_string is the URL
            return format_string
        else:
            if type(single_arg_or_args_tuple) == tuple:
                # URL-encode each arg in the tuple and return it as tuple too
                url_encoded_args = ()
                for arg in single_arg_or_args_tuple:
                    url_encoded_args += (urllib.parse.quote_plus(str(arg)), )
            else:
                # URL-encode single arg
                url_encoded_args = urllib.parse.quote_plus(single_arg_or_args_tuple)

            return format_string % url_encoded_args

    @staticmethod
    def _is_expected_code(code, expected_codes):
        if isinstance(expected_codes, int):
            return code == expected_codes
        elif isinstance(expected_codes, list):
            return code in expected_codes

    @staticmethod
    def _expected_code_to_str(expected_codes):
        if isinstance(expected_codes, int):
            return str(expected_codes)
        elif isinstance(expected_codes, list):
            return ', '.join(map(lambda x: str(x), expected_codes))


class TestRequestFailedException(Exception):
    pass


class ApiVersionIncorrectException(Exception):
    pass


class NotFoundException(Exception):
    pass


class UnexpectedResponseException(Exception):
    pass
