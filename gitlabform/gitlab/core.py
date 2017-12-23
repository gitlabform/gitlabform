import logging
import urllib

import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from gitlabform.configuration.core import ConfigurationCore


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

    def get_project(self, project_and_group_or_id):
        return self._make_requests_to_api("projects/%s", project_and_group_or_id)

    def _get_project_id(self, project_and_group):
        # This is a NEW workaround for https://github.com/gitlabhq/gitlabhq/issues/8290
        result = self.get_project(project_and_group)
        return str(result['id'])

    def _make_requests_to_api(self, path_as_format_string, args=None, method='GET', data=None, expected_codes=200,
                              paginated=False):
        if not paginated:
            response = self._make_request_to_api(path_as_format_string, args, method, data, expected_codes)
            return response.json()
        else:
            if '?' in path_as_format_string:
                path_as_format_string += '&per_page=100'
            else:
                path_as_format_string += '?per_page=100'

            first_response = self._make_request_to_api(path_as_format_string, args, method, data, expected_codes)
            results = first_response.json()
            total_pages = int(first_response.headers['X-Total-Pages'])
            for page in range(2, total_pages + 1):
                response = self._make_request_to_api(path_as_format_string + "&page=" + str(page), args, method, data,
                                                     expected_codes)
                results += response.json()

        return results

    def _make_request_to_api(self, path_as_format_string, args, method, data, expected_codes):
        url = self.url + "/api/v3/" + self._format_with_url_encoding(path_as_format_string, args)
        logging.debug("URL-encoded url=%s" % url)
        headers = {'PRIVATE-TOKEN': self.__token}
        if data:
            response = s.request(method, url, headers=headers, data=data, timeout=10)
        else:
            response = s.request(method, url, headers=headers, timeout=10)
        logging.debug("response code=%s" % response.status_code)
        if response.status_code == 404:
            raise NotFoundException("Resource path='%s' not found!" % url)
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


class NotFoundException(Exception):
    pass


class UnexpectedResponseException(Exception):
    pass
