import os
import re
import sys
from pathlib import Path

from logging import debug, info, warning, critical

from jinja2 import Environment, FileSystemLoader
from gitlab import GitlabGetError, GitlabUpdateError, GitlabListError
from gitlab.v4.objects import Project, ProjectFile, ProjectBranch
from gitlab.base import RESTObject

from gitlabform.constants import EXIT_INVALID_INPUT, EXIT_PROCESSING_ERROR
from gitlabform.configuration import Configuration
from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor
from gitlabform.processors.project.branches_processor import BranchesProcessor


class FilesProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab, config: Configuration, strict: bool):
        super().__init__("files", gitlab)
        self.config = config
        self.strict = strict
        self.branch_processor = BranchesProcessor(gitlab, strict)

    def _process_configuration(self, project_and_group: str, configuration: dict):
        for file in sorted(configuration["files"]):
            project: Project = self.gl.get_project_by_path_cached(project_and_group)
            debug("Processing file '%s'...", file)

            if configuration.get("files|" + file + "|skip"):
                debug("Skipping file '%s'", file)
                continue

            file_config = configuration["files"][file]
            if "branches" not in file_config:
                critical(
                    f"File '{file}' is missing the required 'branches' key."
                    f" Specify which branches to apply the file to using one of:"
                    f" 'all', 'protected', or a list of branch names (e.g. ['main'])."
                )
                sys.exit(EXIT_INVALID_INPUT)

            config_target_ref = file_config["branches"]
            branches_to_update: list[ProjectBranch] = []

            if config_target_ref == "all":
                # Get all Branches in the Project
                branches_to_update.extend(project.branches.list(get_all=True, lazy=True))
            elif config_target_ref == "protected":
                # Get all Protected Branch definitions -> this could return wildcard branch names
                protected_branches = project.protectedbranches.list(get_all=True, lazy=True)
                for protected_branch in protected_branches:
                    self.append_branches_matching_ref(branches_to_update, file, project, protected_branch.name)
            elif isinstance(config_target_ref, list):
                # List of specific branch refs to update -> this could contain wildcard branch names
                for ref in config_target_ref:
                    self.append_branches_matching_ref(branches_to_update, file, project, ref)

            debug(
                "File '%s' to be updated in '%s' branche(s)",
                file,
                len(branches_to_update),
            )

            for branch_to_update in branches_to_update:
                process_only_first: bool = configuration.get("files|" + file + "|only_first_branch", False)

                self.process_branch(branch_to_update, configuration, file, project, project_and_group)

                if process_only_first:
                    info("Skipping other branches for this file, as configured by only_first_branch.")
                    break

    def append_branches_matching_ref(self, branches_to_update: list[ProjectBranch], file, project: Project, ref: str):

        if self.branch_processor.branch_name_contains_supported_wildcard(ref):
            try:
                # GitLab's branches API expects an RE2 regex
                regex_ref = "^" + re.escape(ref).replace(r"\*", ".*") + "$"
                # sorted for deterministic only_first_branch
                wildcard_branches = sorted(
                    project.branches.list(get_all=True, regex=regex_ref),
                    key=lambda b: b.name,
                )
                for wildcard_branch in wildcard_branches:
                    branch_id = wildcard_branch.get_id()
                    if branch_id:
                        branches_to_update.append(wildcard_branch)
            except GitlabListError:
                message = f"! Could not list branches using {ref}, not processing file '{file}' on them"
                if self.strict:
                    critical(message)
                    sys.exit(EXIT_INVALID_INPUT)
                else:
                    warning(message)
        else:
            try:
                branches_to_update.append(project.branches.get(ref))
            except GitlabGetError:
                message = f"! Branch '{ref}' not found, not processing file '{file}' in it"
                if self.strict:
                    critical(message)
                    sys.exit(EXIT_INVALID_INPUT)
                else:
                    warning(message)

    def process_branch(
        self,
        branch: ProjectBranch,
        configuration: dict,
        file: str,
        project: Project,
        project_and_group: str,
    ):
        info(f"Processing file '{file}' in branch '{branch.name}'")

        if configuration.get("files|" + file + "|content") and configuration.get("files|" + file + "|file"):
            critical(
                f"File '{file}' in '{project_and_group}' has both `content` and `file` set - "
                "use only one of these keys."
            )
            sys.exit(EXIT_INVALID_INPUT)

        if configuration.get("files|" + file + "|delete"):
            try:
                file_to_delete: ProjectFile = project.files.get(file_path=file, ref=branch.name)
                debug("Deleting file '%s' in branch '%s'", file, branch.name)
                self.modify_file_dealing_with_branch_protection(
                    project,
                    branch,
                    file_to_delete,
                    "delete",
                    configuration,
                )
            except GitlabGetError:
                debug(
                    "Not deleting file '%s' in branch '%s' (already doesn't exist)",
                    file,
                    branch.name,
                )
        else:
            # change or create file

            if configuration.get("files|" + file + "|content"):
                new_content = configuration.get("files|" + file + "|content")
            else:
                path_in_config = Path(str(configuration.get("files|" + file + "|file")))
                if path_in_config.is_absolute():
                    effective_path = path_in_config
                else:
                    # relative paths are relative to config file location
                    effective_path = Path(os.path.join(self.config.config_dir, str(path_in_config)))
                new_content = effective_path.read_text()

            # templating is documented to be enabled by default,
            # see https://gitlabform.github.io/gitlabform/reference/files/#files
            templating_enabled = True

            if configuration.get("files|" + file + "|template", templating_enabled):
                new_content = self.get_file_content_as_template(
                    new_content,
                    project_and_group,
                    **configuration.get("files|" + file + "|jinja_env", dict()),
                )

            try:
                # Returns base64 encoded content: https://python-gitlab.readthedocs.io/en/stable/gl_objects/projects.html#project-files
                repo_file: ProjectFile = project.files.get(file_path=file, ref=branch.name)
                decoded_file: bytes = repo_file.decode()
                current_content: str = decoded_file.decode("utf-8")

                if current_content != new_content:
                    if configuration.get("files|" + file + "|overwrite"):
                        debug(
                            "Changing file '%s' in branch '%s'",
                            file,
                            branch.name,
                        )
                        self.modify_file_dealing_with_branch_protection(
                            project,
                            branch,
                            repo_file,
                            "modify",
                            configuration,
                            new_content,
                        )
                    else:
                        debug(
                            "Not changing file '%s' in branch '%s' - overwrite flag not set.",
                            file,
                            branch.name,
                        )
                else:
                    debug(
                        "Not changing file '%s' in branch '%s' - it's content is already" " as provided)",
                        file,
                        branch.name,
                    )
            except GitlabGetError:
                debug("Creating file '%s' in branch '%s'", file, branch.name)
                self.modify_file_dealing_with_branch_protection(
                    project,
                    branch,
                    file,
                    "add",
                    configuration,
                    new_content,
                )

    def modify_file_dealing_with_branch_protection(
        self,
        project: Project,
        branch: RESTObject,
        file_to_operate_on: str | ProjectFile,
        operation: str,
        configuration: dict,
        new_content=None,
    ):
        # perhaps your user permissions are ok to just perform this operation regardless
        # of the branch protection...

        try:
            self.just_modify_file(
                project,
                branch,
                file_to_operate_on,
                operation,
                configuration,
                new_content,
            )

        except GitlabUpdateError as e:
            if (
                e.response_code == 400 or e.response_code == 403
            ) and "You are not allowed to push into this branch" in e.error_message:
                # If the project is archived, modifying files is not allowed
                if project.archived:
                    critical(f"Project is archived, cannot modify files in it.: {e.error_message}")
                    sys.exit(EXIT_PROCESSING_ERROR)

                # Otherwise, unprotect the branch but only if we know how to protect it again
                if configuration.get("branches|" + branch.name + "|protected"):
                    debug(f"> Temporarily unprotecting the branch to '{operation}' a file in it...")
                    # Delete operation on protected branch removes the protection only
                    project.protectedbranches.delete(branch.name)
                else:
                    critical(
                        f"Operation '{operation}' on file in branch {branch.name} not permitted."
                        f" We don't have a branch protection configuration provided for this"
                        f" branch. Breaking as we cannot unprotect the branch as we would not know"
                        f" how to protect it again."
                    )
                    sys.exit(EXIT_INVALID_INPUT)

                try:
                    debug("> Attempt updating file again")
                    self.just_modify_file(
                        project,
                        branch,
                        file_to_operate_on,
                        operation,
                        configuration,
                        new_content,
                    )

                finally:
                    # ...and protect the branch again after the operation
                    if configuration.get("branches|" + branch.name + "|protected"):
                        debug("> Protecting the branch again.")
                        branch_config: dict = configuration["branches"][branch.name]
                        self.branch_processor.protect_branch(project, branch.name, branch_config)

            else:
                raise e

    def just_modify_file(
        self,
        project: Project,
        branch: RESTObject,
        file_to_operate_on: str | ProjectFile,
        operation: str,
        configuration: dict,
        new_content=None,
    ):
        if operation == "modify" and isinstance(file_to_operate_on, ProjectFile):
            file_to_operate_on.content = new_content
            file_to_operate_on.save(
                commit_message=self.get_commit_message_for_file_change(
                    "change", file_to_operate_on.file_path, configuration
                ),
                branch=branch.name,
            )
        elif operation == "add" and isinstance(file_to_operate_on, str):
            project.files.create(
                {
                    "file_path": file_to_operate_on,
                    "branch": branch.name,
                    "content": new_content,
                    "commit_message": self.get_commit_message_for_file_change(
                        "delete", file_to_operate_on, configuration
                    ),
                }
            )
        elif operation == "delete" and isinstance(file_to_operate_on, ProjectFile):
            file_to_operate_on.delete(
                commit_message=self.get_commit_message_for_file_change(
                    "delete", file_to_operate_on.file_path, configuration
                ),
                branch=branch.name,
            )

    def get_file_content_as_template(self, template, project_and_group, **kwargs):
        # Use jinja with variables project and group
        rtemplate = Environment(
            loader=FileSystemLoader("."),
            autoescape=True,
            keep_trailing_newline=True,
        ).from_string(template)
        return rtemplate.render(
            project=self.get_project(project_and_group),
            group=self.get_group(project_and_group),
            **kwargs,
        )

    @staticmethod
    def get_commit_message_for_file_change(operation, file, configuration: dict):
        commit_message = configuration.get(
            "files|" + file + "|commit_message",
            "Automated %s made by gitlabform" % operation,
        )

        # add '[skip ci]' to commit message to skip CI job, as documented at
        # https://docs.gitlab.com/ee/ci/yaml/README.html#skipping-jobs
        skip_build = configuration.get("files|" + file + "|skip_ci")
        skip_build_str = " [skip ci]" if skip_build else ""

        return f"{commit_message}{skip_build_str}"

    @staticmethod
    def get_group(project_and_group):
        return re.match("(.*)/.*", project_and_group).group(1)

    @staticmethod
    def get_project(project_and_group):
        return re.match(".*/(.*)", project_and_group).group(1)
