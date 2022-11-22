from tests.acceptance import (
    run_gitlabform,
)


class TestDeployKeysAllProjects:
    def test__deploy_key_to_all_projects(
        self, gitlab, group, project, other_project, public_ssh_key
    ):
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

        deploy_keys1 = gitlab.get_deploy_keys(f"{group}/{project}")
        assert len(deploy_keys1) == 1

        deploy_keys2 = gitlab.get_deploy_keys(f"{group}/{other_project}")
        assert len(deploy_keys2) == 1

    def test__deploy_key_with_spaces_in_comment_to_all_projects(
        self, gitlab, group, project, other_project, public_ssh_key
    ):
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

        deploy_keys1 = gitlab.get_deploy_keys(f"{group}/{project}")
        assert len(deploy_keys1) == 1

        deploy_keys2 = gitlab.get_deploy_keys(f"{group}/{other_project}")
        assert len(deploy_keys2) == 1
