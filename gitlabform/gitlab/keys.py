from gitlabform.gitlab.core import GitLabCore


class GitLabKeys(GitLabCore):

    def get_key(self, id):
        return self._make_requests_to_api("keys/%s", id, 'GET')
