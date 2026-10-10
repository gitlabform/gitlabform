from logging import info, error
from time import sleep

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlab import GitlabGetError, GitlabTransferProjectError
from gitlab.v4.objects import Project


class ProjectProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        project_path_with_namespace: str = project_and_group

        if configuration["project"].get("transfer_from") is not None:
            source_project_path_with_namespace = configuration["project"].get("transfer_from")

            # Check if the project was already transfered (i.e. in previous run) or a project with same path already exists
            try:
                project_in_config: Project = self.gl.get_project_by_path_cached(project_path_with_namespace)
                info(
                    f"Project already exists: '{project_in_config.path_with_namespace}'. Ignoring 'transfer_from' config..."
                )
            except GitlabGetError:
                # Project doesn't exist at the destination. Let's process the transfer request
                project_to_be_transferred: Project = self.gl.get_project_by_path_cached(
                    source_project_path_with_namespace
                )
                destination_project_path = project_and_group.split("/")[-1]
                # Check if the project path needs to be updated; In Gitlab, path maybe different than name
                if destination_project_path != project_to_be_transferred.path:
                    info(
                        f"Updating the source project path from '{project_to_be_transferred.path}' to '{destination_project_path}'"
                    )
                    self.gl.projects.update(project_to_be_transferred.id, {"path": destination_project_path})

                # TODO: Catch GitlabTransferProjectError exception.
                #  See the next comment for details.
                # try:
                project_transfer_destination_group, _ = project_and_group.rsplit("/", 1)
                info(f"Transferring project to '{project_transfer_destination_group}' group...")
                project_to_be_transferred.transfer(project_transfer_destination_group)
                self._wait_for_transfer(project_to_be_transferred.id, project_transfer_destination_group)
                # TODO: Catch GitlabTransferProjectError exception.
                #  The above code can run into exception for various reasons.
                #  We should catch this exception and log a custom error message with hints.
                #  In some scenarios we want to break and in some we want to proceed and attempt a transfer regardless
                #  For more details, see: https://github.com/gitlabform/gitlabform/issues/611
                # except GitlabTransferProjectError as e:
                #     critical(
                #         "Encountered error transferring project. Please check if project transfer requirements were met. Docs: https://docs.gitlab.com/ee/user/project/settings/index.html#transfer-a-project-to-another-namespace"
                #     )
                #     raise

        if configuration["project"].get("archive") is not None:
            project: Project = self.gl.get_project_by_path_cached(project_path_with_namespace)

            if configuration["project"].get("archive") is True:
                info("Archiving project...")
                project.archive()
            elif configuration["project"].get("archive") is False:
                info("Unarchiving project...")
                project.unarchive()

    def _wait_for_transfer(self, project_id: int, destination_group: str) -> None:
        # GitLab 19.4 and newer transfer projects asynchronously, so the API may still
        # report the old namespace right after the transfer request returns
        max_retries = 60
        wait_before_retry = 2
        retry = 0

        while True:
            current_namespace = self.gl.projects.get(project_id).namespace["full_path"]

            if current_namespace == destination_group:
                return

            retry += 1

            if retry > max_retries:
                raise GitlabTransferProjectError(
                    f"Project is still in '{current_namespace}' after waiting for the transfer"
                    f" to '{destination_group}' to complete"
                )

            sleep(wait_before_retry)
