from cli_ui import debug as verbose
from logging import fatal
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.gitlab import GitlabWrapper
from gitlab import Gitlab, GitlabGetError, GitlabTransferProjectError
from gitlab.v4.objects import Project


class ProjectProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("project", gitlab)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        if configuration["project"].get("transfer_from") is not None:
            source_project_path_with_namespace = configuration["project"].get(
                "transfer_from"
            )
            destination_project_path_with_namespace = project_and_group
            gl: Gitlab = GitlabWrapper(self.gitlab)._gitlab

            # Check if the project was already transfered (i.e. in previous run) or a project with same path already exists
            try:
                project: Project = gl.projects.get(
                    destination_project_path_with_namespace
                )
                verbose(
                    "Project already exists: '"
                    + project.path_with_namespace
                    + "'. Ignoring 'transfer_from' config..."
                )
            except GitlabGetError:
                # Project doesn't exist at the destination. Let's process the transfer request
                project_to_be_transferred: Project = gl.projects.get(
                    source_project_path_with_namespace
                )
                destination_project_path = project_and_group.split("/")[-1]
                # Check if the project path needs to be updated; In Gitlab, path maybe different than name
                if destination_project_path != project_to_be_transferred.path:
                    verbose(
                        "Updating the source project path from '"
                        + project_to_be_transferred.path
                        + "' to '"
                        + destination_project_path
                    )
                    gl.projects.update(
                        project_to_be_transferred.id, {"path": destination_project_path}
                    )

                try:
                    project_transfer_destination_group, _ = project_and_group.rsplit(
                        "/", 1
                    )
                    verbose(
                        "Transferring project to '"
                        + project_transfer_destination_group
                        + "' group..."
                    )
                    project_to_be_transferred.transfer(
                        project_transfer_destination_group
                    )
                except GitlabTransferProjectError:
                    fatal(
                        "Encountered error transferring project. Please check if project transfer requirements were met. Docs: https://docs.gitlab.com/ee/user/project/settings/index.html#transfer-a-project-to-another-namespace"
                    )
                    raise

        if configuration["project"].get("archive") is not None:
            if configuration["project"].get("archive") is True:
                verbose("Archiving project...")
                self.gitlab.archive(project_and_group)
            elif configuration["project"].get("archive") is False:
                verbose("Unarchiving project...")
                self.gitlab.unarchive(project_and_group)
