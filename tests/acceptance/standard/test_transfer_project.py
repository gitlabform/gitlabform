from tests.acceptance import (
    get_random_suffix,
    run_gitlabform,
)
from gitlabform.gitlab import AccessLevel
from gitlab import GitlabTransferProjectError
import re
import pytest


class TestTransferProject:
    def test__transfer_between_two_root_groups_dry_run(
        self, project_for_function, group, other_group
    ):
        project_new_path_with_namespace = (
            f"{other_group.path}/{project_for_function.name}"
        )
        projects_in_destination_before_transfer = other_group.projects.list()

        config = f"""
        projects_and_groups:
          {project_new_path_with_namespace}:
            project:
              transfer_from: {project_for_function.path_with_namespace}
            project_settings:
              description: test
        """

        run_gitlabform(
            config, project_new_path_with_namespace, noop=True, output_file="output.yml"
        )
        projects_in_destination_after_transfer = other_group.projects.list()

        assert len(projects_in_destination_after_transfer) == len(
            projects_in_destination_before_transfer
        )

    def test__transfer_between_two_root_groups(
        self, project_for_function, group, other_group
    ):
        project_new_path_with_namespace = (
            f"{other_group.path}/{project_for_function.name}"
        )
        projects_in_destination_before_transfer = other_group.projects.list()

        config = f"""
        projects_and_groups:
          {project_for_function.path_with_namespace}/*:
            project_settings:
              description: test

          {project_new_path_with_namespace}:
            project:
              transfer_from: {project_for_function.path_with_namespace}
        """

        run_gitlabform(config, project_new_path_with_namespace)
        projects_in_destination_after_transfer = other_group.projects.list()

        assert (
            len(projects_in_destination_after_transfer)
            == len(projects_in_destination_before_transfer) + 1
        )

    def test__transfer_between_root_group_and_subgroup(
        self, project_in_subgroup, group, subgroup
    ):
        project_new_path_with_namespace = f"{group.path}/{project_in_subgroup.name}"
        projects_in_destination_before_transfer = group.projects.list()

        config = f"""
        projects_and_groups:
          {project_new_path_with_namespace}:
            project:
              transfer_from: {project_in_subgroup.path_with_namespace}
        """

        run_gitlabform(config, project_new_path_with_namespace)
        projects_in_destination_after_transfer = group.projects.list()

        assert (
            len(projects_in_destination_after_transfer)
            == len(projects_in_destination_before_transfer) + 1
        )

    def test__transfer_as_same_path_at_namespae_already_exist(
        self, project_for_function, group, other_group
    ):
        project_new_path_with_namespace = (
            f"{other_group.path}/{project_for_function.name}"
        )
        projects_in_destination_before_transfer = other_group.projects.list()

        config = f"""
        projects_and_groups:
          {project_new_path_with_namespace}:
            project:
              transfer_from: {project_for_function.path_with_namespace}
        """

        run_gitlabform(config, project_new_path_with_namespace)
        projects_in_destination_after_transfer = other_group.projects.list()

        assert (
            len(projects_in_destination_after_transfer)
            == len(projects_in_destination_before_transfer) + 1
        )

        # Now re-run gitlabform with the same config.
        # Since the transfer is already done above, the 2nd run should not try to perform transfer again.
        run_gitlabform(config, project_new_path_with_namespace)
        projects_in_destination_after_transfer_second_run = other_group.projects.list()

        assert len(projects_in_destination_after_transfer_second_run) == len(
            projects_in_destination_after_transfer
        )
        assert (
            len(projects_in_destination_after_transfer_second_run)
            == len(projects_in_destination_before_transfer) + 1
        )

    def test__transfer_as_different_path(
        self, gl, project_for_function, group, other_group
    ):
        project_source_path_with_namespace = project_for_function.path_with_namespace
        project_new_path = project_for_function.path + "_" + get_random_suffix()
        project_new_path_with_namespace = f"{other_group.path}/{project_new_path}"
        projects_in_new_path_before_transfer = other_group.projects.list()

        config = f"""
        projects_and_groups:
          {project_new_path_with_namespace}:
            project:
              transfer_from: {project_source_path_with_namespace}
        """

        run_gitlabform(config, project_new_path_with_namespace)

        projects_in_new_path_after_transfer = other_group.projects.list()
        assert (
            len(projects_in_new_path_after_transfer)
            == len(projects_in_new_path_before_transfer) + 1
        )

        project_after_transfer = gl.projects.get(project_for_function.id)
        assert project_for_function.path != project_after_transfer.path
        assert project_after_transfer.path == project_new_path
        assert (
            project_after_transfer.path_with_namespace
            == project_new_path_with_namespace
        )

    def test__transfer_and_update(self, gl, project_for_function, group, other_group):
        assert project_for_function.visibility == "private"
        assert project_for_function.description is None

        project_name = project_for_function.name
        project_description = "Some description for testing"
        project_source_path_with_namespace = project_for_function.path_with_namespace
        project_new_path_with_namespace = f"{other_group.path}/{project_name}"
        projects_in_new_path_before_transfer = other_group.projects.list()

        config = f"""
        projects_and_groups:
          {project_new_path_with_namespace}:
            project:
              transfer_from: {project_source_path_with_namespace}
            project_settings:
              visibility: internal
              description: {project_description}
            branches:
              foo-bar:
                protected: true
                merge_access_level: {AccessLevel.DEVELOPER.value}
        """

        run_gitlabform(config, project_new_path_with_namespace)
        projects_in_new_path_after_transfer = other_group.projects.list()

        assert (
            len(projects_in_new_path_after_transfer)
            == len(projects_in_new_path_before_transfer) + 1
        )
        project_after_transfer = gl.projects.get(project_for_function.id)
        assert project_after_transfer.visibility == "internal"
        assert project_after_transfer.description == project_description
        # When a project is created, it already comes with 'main' as default protected branch.
        # We want to assert that we have an additional protected branch
        assert len(project_after_transfer.protectedbranches.list()) == 2
        assert project_after_transfer.protectedbranches.list()[1].name == "foo-bar"

    def test__transfer_and_archive(self, gl, project_for_function, group, other_group):
        project_name = project_for_function.name
        project_source_path = project_for_function.path_with_namespace
        project_new_path_with_namespace = f"{other_group.path}/{project_name}"
        projects_in_new_path_before_transfer = other_group.projects.list()

        config = f"""
        projects_and_groups:
          {project_new_path_with_namespace}:
            project:
              archive: true
              transfer_from: {project_source_path}
        """

        run_gitlabform(config, project_new_path_with_namespace)

        projects_in_new_path_after_transfer = other_group.projects.list()
        assert (
            len(projects_in_new_path_after_transfer)
            == len(projects_in_new_path_before_transfer) + 1
        )

        project_after_transfer = gl.projects.get(project_for_function.id)
        assert project_after_transfer.archived is True

    # It seems Gitlab allows moving/transferring a project that is already archived.
    # This test case validates that. The project will still be in archived state but
    # it is allowed to be transferred.
    def test__transfer_project_already_archived(
        self, gl, project_for_function, group, other_group
    ):
        project_name = project_for_function.name
        project_source_path = project_for_function.path_with_namespace
        project_new_path_with_namespace = f"{other_group.path}/{project_name}"
        projects_in_new_path_before_transfer = other_group.projects.list()

        config = f"""
        projects_and_groups:
          {project_new_path_with_namespace}:
            project:
              transfer_from: {project_source_path}
        """

        # Archive the project before we run gitlabform
        gl.projects.get(project_for_function.id).archive()

        run_gitlabform(config, project_new_path_with_namespace)

        projects_in_new_path_after_transfer = other_group.projects.list()
        assert (
            len(projects_in_new_path_after_transfer)
            == len(projects_in_new_path_before_transfer) + 1
        )

        project_after_transfer = gl.projects.get(project_for_function.id)
        assert project_after_transfer.archived is True

    def test__transfer_and_unarchive(
        self, gl, project_for_function, group, other_group
    ):
        project_name = project_for_function.name
        project_source_path = project_for_function.path_with_namespace
        project_new_path = project_for_function.path + "_" + get_random_suffix()
        project_new_path_with_namespace = f"{other_group.path}/{project_new_path}"
        projects_in_new_path_before_transfer = other_group.projects.list()

        config = f"""
        projects_and_groups:
          {project_new_path_with_namespace}:
            project:
              archive: false
              transfer_from: {project_source_path}
        """

        # Archive the project before we run gitlabform
        gl.projects.get(project_for_function.id).archive()

        run_gitlabform(config, project_new_path_with_namespace)

        projects_in_new_path_after_transfer = other_group.projects.list()
        assert (
            len(projects_in_new_path_after_transfer)
            == len(projects_in_new_path_before_transfer) + 1
        )

        project_after_transfer = gl.projects.get(project_for_function.id)
        assert project_after_transfer.archived is False
        assert project_for_function.path != project_after_transfer.path
        assert project_after_transfer.path == project_new_path
        assert (
            project_after_transfer.path_with_namespace
            == project_new_path_with_namespace
        )

    # This test serves validation of project transfer error handling.
    # There are several requirements or prerequisites from Gitlab for
    # transferring a project to another group or namespace. Details
    # are available at https://docs.gitlab.com/ee/user/project/settings/index.html#transfer-a-project-to-another-namespace.
    # Cannot test all the prerequisites because that will require extra
    # fixture or running gitlabform as a different user.
    #
    # This test is passing at the moment, but it's not properly capturing
    # or validating the exception. That's why it's marked to be skipped. It
    # should be enabled and fixed when 'GitlabTransferProjectError' exception
    # is caught in the code, potentially with custom messages. For more details,
    # see: https://github.com/gitlabform/gitlabform/issues/611
    @pytest.mark.skip(
        reason="Need to wait till exception handling with custom message is implemented."
    )
    def test__transfer_without_satisfied_prerequisites(
        self, gl, project_for_function, other_group
    ):
        project_name = project_for_function.name
        project_source_path = project_for_function.path_with_namespace
        project_new_path_with_namespace = f"{other_group.path}/{project_name}"
        projects_in_new_path_before_transfer = other_group.projects.list()

        config = f"""
        projects_and_groups:
          {project_new_path_with_namespace}:
            project:
              transfer_from: {project_source_path}
        """

        # Before running gitlabform, update the destination group so that
        # new project creation is disabled. Then run gitlabform. This will
        # violate one of the requirements for project transfer (access to
        # create project in destination namespace).
        gl.groups.update(other_group.id, {"project_creation_level": "noone"})

        with pytest.raises(SystemExit):
            with pytest.raises(
                GitlabTransferProjectError, match=r".*error transferring project.*"
            ):
                run_gitlabform(config, project_new_path_with_namespace)

        projects_in_new_path_after_transfer = other_group.projects.list()
        assert len(projects_in_new_path_after_transfer) == len(
            projects_in_new_path_before_transfer
        )

    def test__transfer_with_target_all_defined(
        self, project_for_function, group, other_group
    ):
        project_new_path_with_namespace = (
            f"{other_group.path}/{project_for_function.name}"
        )
        projects_in_destination_before_transfer = other_group.projects.list()

        config = f"""
        projects_and_groups:
          {group.path}/*:
            project_settings:
              description: test
          {project_new_path_with_namespace}:
            project:
              transfer_from: {project_for_function.path_with_namespace}
        """

        run_gitlabform(config, "ALL_DEFINED")
        projects_in_destination_after_transfer = other_group.projects.list()

        assert (
            len(projects_in_destination_after_transfer)
            == len(projects_in_destination_before_transfer) + 1
        )

    def test__transfer_with_target_all(self, project_for_function, group, other_group):
        project_new_path_with_namespace = (
            f"{other_group.path}/{project_for_function.name}"
        )
        projects_in_destination_before_transfer = other_group.projects.list()

        config = f"""
        projects_and_groups:
          {project_new_path_with_namespace}:
            project:
              transfer_from: {project_for_function.path_with_namespace}
        """

        run_gitlabform(config, "ALL")
        projects_in_destination_after_transfer = other_group.projects.list()

        assert (
            len(projects_in_destination_after_transfer)
            == len(projects_in_destination_before_transfer) + 1
        )

    def test__transfer_with_target_group(
        self, project_for_function, group, other_group
    ):
        project_new_path_with_namespace = (
            f"{other_group.path}/{project_for_function.name}"
        )
        projects_in_destination_before_transfer = other_group.projects.list()

        config = f"""
        projects_and_groups:
          {project_new_path_with_namespace}:
            project:
              transfer_from: {project_for_function.path_with_namespace}
        """

        run_gitlabform(config, other_group.path)
        projects_in_destination_after_transfer = other_group.projects.list()

        assert (
            len(projects_in_destination_after_transfer)
            == len(projects_in_destination_before_transfer) + 1
        )

    def test__transfer_with_target_sub_group(
        self, project_in_subgroup, group, other_subgroup
    ):
        project_new_path_with_namespace = (
            f"{group.path}/{other_subgroup.path}/{project_in_subgroup.name}"
        )
        projects_in_destination_before_transfer = other_subgroup.projects.list()

        config = f"""
        projects_and_groups:
          {project_new_path_with_namespace}:
            project:
              transfer_from: {project_in_subgroup.path_with_namespace}
        """

        run_gitlabform(config, f"{group.path}/{other_subgroup.path}")
        projects_in_destination_after_transfer = other_subgroup.projects.list()

        assert (
            len(projects_in_destination_after_transfer)
            == len(projects_in_destination_before_transfer) + 1
        )

    def test__transfer_non_existing_project(
        self, project_for_function, group, other_group
    ):
        project_new_path_with_namespace = (
            f"{other_group.path}/{project_for_function.name}"
        )

        config = f"""
        projects_and_groups:
          {project_new_path_with_namespace}:
            project:
              transfer_from: non/existent_project
        """

        with pytest.raises(SystemExit):
            run_gitlabform(config, project_new_path_with_namespace)
