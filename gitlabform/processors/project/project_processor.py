from cli_ui import debug
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlab import GitlabGetError
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
                debug(
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
                    debug(
                        f"Updating the source project path from '{project_to_be_transferred.path}' to '{destination_project_path}'"
                    )
                    self.gl.projects.update(project_to_be_transferred.id, {"path": destination_project_path})

                # TODO: Catch GitlabTransferProjectError exception.
                #  See the next comment for details.
                # try:
                project_transfer_destination_group, _ = project_and_group.rsplit("/", 1)
                debug(f"Transferring project to '{project_transfer_destination_group}' group...")
                project_to_be_transferred.transfer(project_transfer_destination_group)
                # TODO: Catch GitlabTransferProjectError exception.
                #  The above code can run into exception for various reasons.
                #  We should catch this exception and log a custom error message with hints.
                #  For more details, see: https://github.com/gitlabform/gitlabform/issues/611
                # except GitlabTransferProjectError as e:
                #     fatal(
                #         "Encountered error transferring project. Please check if project transfer requirements were met. Docs: https://docs.gitlab.com/ee/user/project/settings/index.html#transfer-a-project-to-another-namespace"
                #     )
                #     raise

        if configuration["project"].get("archive") is not None:
            project: Project = self.gl.get_project_by_path_cached(project_path_with_namespace)

            if configuration["project"].get("archive") is True:
                debug("Archiving project...")
                project.archive()
            elif configuration["project"].get("archive") is False:
                debug("Unarchiving project...")
                project.unarchive()
