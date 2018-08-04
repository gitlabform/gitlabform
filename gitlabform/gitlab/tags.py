from gitlabform.gitlab.core import GitLabCore


class GitLabTags(GitLabCore):

    def get_tags(self, project_and_group_name):
        return self._make_requests_to_api("projects/%s/repository/tags", project_and_group_name)

    def create_tag(self, project_and_group_name, tag_name, ref, message=None):
        data = {
            'tag_name': tag_name,
            'ref': ref,
            'message': message,
        }
        return self._make_requests_to_api("projects/%s/repository/tags", project_and_group_name, method='POST', data=data,
                                          expected_codes=201)
