from tests.acceptance import (
    run_gitlabform,
)


class TestDeployKeysAllProjects:
    def test__deploy_key_to_all_projects(self, group, project, other_project, public_ssh_key):
        deploy_key_to_all_projects = f"""
        projects_and_groups:
          "*":
            deploy_keys:
              foobar:
                key: {public_ssh_key}
                title: common_key
                can_push: false
        """
        run_gitlabform(deploy_key_to_all_projects, group.full_path)

        assert len(project.keys.list()) == 1
        assert len(other_project.keys.list()) == 1

    def test__deploy_key_with_spaces_in_comment_to_all_projects(self, group, project, other_project, public_ssh_key):
        public_ssh_key = f"{public_ssh_key} this is a comment with spaces"

        deploy_key_to_all_projects = f"""
        projects_and_groups:
          "*":
            deploy_keys:
              foobar:
                key: {public_ssh_key}
                title: common_key
                can_push: false
        """
        run_gitlabform(deploy_key_to_all_projects, group)

        assert len(project.keys.list()) == 1
        assert len(other_project.keys.list()) == 1
