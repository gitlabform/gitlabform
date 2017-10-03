from gitlabform.gitlab.core import GitLabCore


class GitLabGroups(GitLabCore):

    def get_groups(self):
        """
        :return: sorted list of groups
        """
        result = self._make_requests_to_api("/groups?all_available=true", paginated=True)
        return sorted(map(lambda x: x['path'], result))
