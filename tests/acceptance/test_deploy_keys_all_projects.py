from tests.acceptance import (
    run_gitlabform,
)


class TestDeployKeysAllProjects:
    def test__deploy_key_to_all_projects(self, gitlab, group, project, other_project):
        # noinspection PyPep8
        deploy_key_to_all_projects = """
        projects_and_groups:
          "*":
            deploy_keys:
              foobar:
                key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC6OxCCViSjh8QUKNOoGqhUqs4LLDMyq/7DYuvMJu5lXwECWp0wFGoLXzYWCT6WOAP+vccncOrlVfsr9VJzXxR1QZq+p3joW25nWgjEw/HCPI6fnU1vROImzxnvwLS3EEJpy64Jq0FFwjt8vKSuQshPysEBSUTf5t3omb166MGlZ+Y6/tOf/8/3zqmvb8OqNmhUtfwxfE5oX8Z8bBaGrkxHlmYyJ9UBpfeEcFt1GqfiONPgchJJ4OqCJKqd7H4DZOosT64kTqPXhca44EOxiKQviCthv7bO+r7VSFo5TVo60ikq/sTR9ifXnd3B9x3LV1qzHHLlmnP//xkKHIZGxfyhgwtdGNWhEtKPiXUzZv4/48WUJMmtpjznhuEgjnpiJL3x0+vJCStA6WG0MiozBlS80Y4XHbt3X3bvlNSqSo/GpnxlPTUx+Lj/ASI75JDym14+C8RdSFN4iKl5Qjz5xFq4eXke00AahFvjAAV5BT8Qrlyg/cbt1pfWKND1T5Fqh6c=
                title: common_key
                can_push: false
        """
        run_gitlabform(deploy_key_to_all_projects, group)

        deploy_keys1 = gitlab.get_deploy_keys(f"{group}/{project}")
        assert len(deploy_keys1) == 1

        deploy_keys2 = gitlab.get_deploy_keys(f"{group}/{other_project}")
        assert len(deploy_keys2) == 1
