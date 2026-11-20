from tests.acceptance import run_gitlabform

WEEKEND = ("0 23 * * 5", "0 7 * * 1", "Europe/Paris")
CHRISTMAS = ("0 0 24 12 *", "0 0 26 12 *", "UTC")
NEW_YEAR = ("0 0 31 12 *", "0 0 2 1 *", "UTC")


def list_freezes(project) -> list[dict]:
    return project.manager.gitlab.http_list(f"/projects/{project.id}/freeze_periods", get_all=True)


def freezes(project) -> list[tuple[str, str, str]]:
    return sorted((p["freeze_start"], p["freeze_end"], p["cron_timezone"]) for p in list_freezes(project))


def freeze_ids(project) -> set[int]:
    return {p["id"] for p in list_freezes(project)}


class TestDeployFreezes:
    def test_create_and_idempotency(self, project):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            deploy_freezes:
              periods:
                - freeze_start: "{WEEKEND[0]}"
                  freeze_end: "{WEEKEND[1]}"
                  cron_timezone: {WEEKEND[2]}
                - freeze_start: "{CHRISTMAS[0]}"
                  freeze_end: "{CHRISTMAS[1]}"
        """

        run_gitlabform(config, project)
        ids_after_first_run = freeze_ids(project)
        run_gitlabform(config, project)

        assert freezes(project) == sorted([WEEKEND, CHRISTMAS])
        assert freeze_ids(project) == ids_after_first_run

    def test_without_enforce_others_are_kept(self, project):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            deploy_freezes:
              periods:
                - freeze_start: "{WEEKEND[0]}"
                  freeze_end: "{WEEKEND[1]}"
                  cron_timezone: {WEEKEND[2]}
                - freeze_start: "{NEW_YEAR[0]}"
                  freeze_end: "{NEW_YEAR[1]}"
        """

        run_gitlabform(config, project)

        assert freezes(project) == sorted([WEEKEND, CHRISTMAS, NEW_YEAR])

    def test_enforce_deletes_others(self, project):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            deploy_freezes:
              enforce: true
              periods:
                - freeze_start: "{WEEKEND[0]}"
                  freeze_end: "{WEEKEND[1]}"
                  cron_timezone: {WEEKEND[2]}
                - freeze_start: "{NEW_YEAR[0]}"
                  freeze_end: "{NEW_YEAR[1]}"
        """

        run_gitlabform(config, project)

        assert freezes(project) == sorted([WEEKEND, NEW_YEAR])

    def test_empty_list_without_enforce_keeps_all(self, project):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            deploy_freezes:
              periods: []
        """

        run_gitlabform(config, project)

        assert freezes(project) == sorted([WEEKEND, NEW_YEAR])

    def test_enforce_with_empty_list_deletes_all(self, project):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            deploy_freezes:
              enforce: true
              periods: []
        """

        run_gitlabform(config, project)

        assert freezes(project) == []

    def test_duplicates_are_deleted(self, project):
        path = f"/projects/{project.id}/freeze_periods"
        payload = {"freeze_start": WEEKEND[0], "freeze_end": WEEKEND[1], "cron_timezone": WEEKEND[2]}
        seeded_ids = {project.manager.gitlab.http_post(path, post_data=payload)["id"] for _ in range(2)}
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            deploy_freezes:
              periods:
                - freeze_start: "{WEEKEND[0]}"
                  freeze_end: "{WEEKEND[1]}"
                  cron_timezone: {WEEKEND[2]}
        """

        run_gitlabform(config, project)

        assert freezes(project) == [WEEKEND]
        assert len(freeze_ids(project) & seeded_ids) == 1
