import pytest

from gitlabform.configuration import Configuration
from gitlabform.configuration.core import ConfigurationCore


@pytest.fixture
def configuration_with_exact_and_recursive():
    config_yaml = """
    ---
    projects_and_groups:
      "*":
        group_settings:
          setting_from_common: common_value

      some_group/*:
        group_settings:
          visibility: private
          description: "recursive description"

      some_group/:
        group_settings:
          visibility: public
          ai_settings_attributes:
            ai_catalog_restricted_to_group_hierarchy: true

      some_group/subgroup/*:
        group_settings:
          project_creation_level: developer

      some_group/subgroup/:
        group_settings:
          description: "subgroup only description"
    """
    return Configuration(config_string=config_yaml)


class TestEffectiveConfigResolution:
    def test__exact_config__overrides_recursive_for_same_group(self, configuration_with_exact_and_recursive):
        effective_config = configuration_with_exact_and_recursive.get_effective_config_for_group("some_group")

        group_settings = effective_config["group_settings"]

        assert group_settings["visibility"] == "public"
        assert group_settings["ai_settings_attributes"] == {"ai_catalog_restricted_to_group_hierarchy": True}

    def test__exact_config__does_not_cascade_to_subgroups(self, configuration_with_exact_and_recursive):
        effective_config = configuration_with_exact_and_recursive.get_effective_config_for_group("some_group/subgroup")

        group_settings = effective_config["group_settings"]

        assert "ai_settings_attributes" not in group_settings
        assert group_settings["visibility"] == "private"
        assert group_settings["project_creation_level"] == "developer"

    def test__exact_config__subgroup_exact_does_not_cascade(self, configuration_with_exact_and_recursive):
        effective_config = configuration_with_exact_and_recursive.get_effective_config_for_group(
            "some_group/subgroup/child"
        )

        group_settings = effective_config["group_settings"]

        assert group_settings.get("description") == "recursive description"
        assert "subgroup only description" not in str(group_settings)

    def test__exact_config__common_merges_with_exact(self, configuration_with_exact_and_recursive):
        effective_config = configuration_with_exact_and_recursive.get_effective_config_for_group("some_group")

        assert effective_config["group_settings"]["setting_from_common"] == "common_value"

    def test__exact_only__no_recursive_defined(self):
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            group_settings:
              setting_from_common: common_value

          my_group/:
            group_settings:
              visibility: public
        """
        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_group("my_group")

        assert effective_config == {
            "group_settings": {
                "setting_from_common": "common_value",
                "visibility": "public",
            },
        }

    def test__recursive_only__no_exact_defined(self, configuration_with_exact_and_recursive):
        effective_config = configuration_with_exact_and_recursive.get_effective_config_for_group("some_group/subgroup")

        assert effective_config["group_settings"]["project_creation_level"] == "developer"
        assert effective_config["group_settings"]["visibility"] == "private"


class TestInheritFalseInteraction:
    def test__exact_config__inherit_false_breaks_from_recursive(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            group_settings:
              visibility: private
              description: "recursive description"

          some_group/:
            group_settings:
              inherit: false
              visibility: public
        """
        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_group("some_group")

        assert effective_config == {
            "group_settings": {
                "visibility": "public",
            },
        }

    def test__exact_config__inherit_false_common_still_merges(self):
        """inherit: false in exact config breaks from the recursive layer,
        but common (*) config still merges — consistent with existing behavior
        where inherit: false only breaks from the immediate parent in the merge chain."""
        config_yaml = """
        ---
        projects_and_groups:
          "*":
            group_settings:
              setting_from_common: common_value

          some_group/*:
            group_settings:
              visibility: private

          some_group/:
            group_settings:
              inherit: false
              visibility: public
        """
        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_group("some_group")

        # inherit: false breaks from recursive (so "visibility: private" is dropped),
        # but common config still merges in
        assert effective_config["group_settings"] == {
            "setting_from_common": "common_value",
            "visibility": "public",
        }


class TestGetGroupsAndKeyType:
    def test__get_groups__returns_exact_groups(self):
        config_yaml = """
        ---
        projects_and_groups:
          my_group/:
            group_settings:
              visibility: public
        """
        configuration = Configuration(config_string=config_yaml)

        groups = configuration.get_groups()

        assert "my_group" in groups

    def test__get_groups__deduplicates_exact_and_recursive(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            group_settings:
              visibility: private

          some_group/:
            group_settings:
              visibility: public
        """
        configuration = Configuration(config_string=config_yaml)

        groups = configuration.get_groups()

        assert groups.count("some_group") == 1

    def test__get_key_type__group_exact(self):
        assert ConfigurationCore._get_key_type("some_group/") == "group_exact"
        assert ConfigurationCore._get_key_type("some_group/subgroup/") == "group_exact"

    def test__get_key_type__existing_types_unchanged(self):
        assert ConfigurationCore._get_key_type("*") == "common"
        assert ConfigurationCore._get_key_type("g/*") == "group"
        assert ConfigurationCore._get_key_type("g/p") == "project"
        assert ConfigurationCore._get_key_type("g/p*") == "project_pattern"


class TestProjectExclusion:
    def test__get_projects__excludes_exact_group_keys(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/:
            group_settings:
              visibility: public

          some_group/some_project:
            project_settings:
              foo: bar
        """
        configuration = Configuration(config_string=config_yaml)

        projects = configuration.get_projects()

        assert "some_group/" not in projects
        assert "some_group/some_project" in projects

    def test__get_effective_config_for_project__exact_group_config_applies(self):
        config_yaml = """
        ---
        projects_and_groups:
          some_group/*:
            project_settings:
              setting_from_recursive: foo

          some_group/:
            group_settings:
              visibility: public

          some_group/my_project:
            project_settings:
              setting_from_project: bar
        """
        configuration = Configuration(config_string=config_yaml)

        effective_config = configuration.get_effective_config_for_project("some_group/my_project")

        assert effective_config["group_settings"]["visibility"] == "public"
        assert effective_config["project_settings"]["setting_from_recursive"] == "foo"
        assert effective_config["project_settings"]["setting_from_project"] == "bar"
