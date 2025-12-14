"""
Unit tests for custom YAML tags support in GitLabForm configuration v5.
"""

import logging
import pathlib
import tempfile
import pytest

import ruamel.yaml

from gitlabform.configuration.yaml_tags import (
    GitLabFormTagOrderedDict,
    GitLabFormTagScalar,
    GitLabFormTagList,
    InheritEnum,
    register_custom_tags,
)

logger = logging.getLogger(__name__)


@pytest.fixture
def yaml_parser():
    """Create a YAML parser with custom tags registered."""
    yaml = ruamel.yaml.YAML()
    register_custom_tags(yaml)
    return yaml


class TestInheritTag:
    """Tests for the !inherit tag."""

    def test_inherit_scalar_force(self, yaml_parser):
        """Test !inherit with force value."""
        data = """
        project_settings: !inherit force
        """
        parsed_data = yaml_parser.load(data)
        assert isinstance(parsed_data["project_settings"], GitLabFormTagOrderedDict)
        assert parsed_data["project_settings"].get_tag("inherit") == "force"

    def test_inherit_scalar_never(self, yaml_parser):
        """Test !inherit with never value."""
        data = """
        settings: !inherit never
        """
        parsed_data = yaml_parser.load(data)
        assert isinstance(parsed_data["settings"], GitLabFormTagOrderedDict)
        assert parsed_data["settings"].get_tag("inherit") == "never"

    def test_inherit_scalar_always(self, yaml_parser):
        """Test !inherit with always value."""
        data = """
        settings: !inherit always
        """
        parsed_data = yaml_parser.load(data)
        assert isinstance(parsed_data["settings"], GitLabFormTagOrderedDict)
        assert parsed_data["settings"].get_tag("inherit") == "always"

    def test_inherit_scalar_true(self, yaml_parser):
        """Test !inherit with true value."""
        data = """
        settings: !inherit true
        """
        parsed_data = yaml_parser.load(data)
        assert isinstance(parsed_data["settings"], GitLabFormTagOrderedDict)
        assert parsed_data["settings"].get_tag("inherit") == "true"

    def test_inherit_scalar_false(self, yaml_parser):
        """Test !inherit with false value."""
        data = """
        settings: !inherit false
        """
        parsed_data = yaml_parser.load(data)
        assert isinstance(parsed_data["settings"], GitLabFormTagOrderedDict)
        assert parsed_data["settings"].get_tag("inherit") == "false"

    def test_inherit_with_sequence_and_keep_existing(self, yaml_parser):
        """Test !inherit with sequence containing keep_existing."""
        data = """
        settings: !inherit [always, keep_existing]
        """
        parsed_data = yaml_parser.load(data)
        assert isinstance(parsed_data["settings"], GitLabFormTagList)
        assert parsed_data["settings"].get_tag("inherit") == "always"
        assert parsed_data["settings"].get_tag("keep_existing") is True

    def test_inherit_invalid_value(self, yaml_parser):
        """Test !inherit with invalid value raises error."""
        data = """
        settings: !inherit invalid_value
        """
        with pytest.raises(ValueError, match="Invalid inherit value"):
            yaml_parser.load(data)

    def test_inherit_with_invalid_combination(self, yaml_parser):
        """Test !inherit with invalid tag combination raises error."""
        data = """
        settings: !inherit [always, invalid_tag]
        """
        with pytest.raises(ValueError, match="Invalid combination of tags"):
            yaml_parser.load(data)


class TestEnforceTag:
    """Tests for the !enforce tag."""

    def test_enforce_mapping(self, yaml_parser):
        """Test !enforce on mapping node."""
        data = """
        project_settings:
          !enforce
          topics:
            - topicA
            - topicB
        """
        parsed_data = yaml_parser.load(data)
        assert isinstance(parsed_data["project_settings"], GitLabFormTagOrderedDict)
        assert parsed_data["project_settings"].get_tag("enforce") is True
        assert "topics" in parsed_data["project_settings"]
        assert parsed_data["project_settings"]["topics"] == ["topicA", "topicB"]

    def test_enforce_with_nested_structure(self, yaml_parser):
        """Test !enforce with nested configuration."""
        data = """
        settings:
          !enforce
          variables:
            VAR1: value1
            VAR2: value2
          deploy_keys:
            key1:
              title: Key 1
              can_push: false
        """
        parsed_data = yaml_parser.load(data)
        assert isinstance(parsed_data["settings"], GitLabFormTagOrderedDict)
        assert parsed_data["settings"].get_tag("enforce") is True
        assert "variables" in parsed_data["settings"]
        assert "deploy_keys" in parsed_data["settings"]


class TestDeleteTag:
    """Tests for the !delete tag."""

    def test_delete_scalar(self, yaml_parser):
        """Test !delete on scalar value."""
        data = """
        topics:
          - !delete topicA
          - topicB
        """
        parsed_data = yaml_parser.load(data)
        assert isinstance(parsed_data["topics"][0], GitLabFormTagScalar)
        assert parsed_data["topics"][0].value == "topicA"
        assert parsed_data["topics"][0].get_tag("delete") is True
        assert parsed_data["topics"][1] == "topicB"

    def test_delete_multiple_items(self, yaml_parser):
        """Test !delete on multiple items."""
        data = """
        items:
          - !delete item1
          - item2
          - !delete item3
          - item4
        """
        parsed_data = yaml_parser.load(data)
        items = parsed_data["items"]
        assert isinstance(items[0], GitLabFormTagScalar)
        assert items[0].get_tag("delete") is True
        assert items[1] == "item2"
        assert isinstance(items[2], GitLabFormTagScalar)
        assert items[2].get_tag("delete") is True
        assert items[3] == "item4"


class TestKeepExistingTag:
    """Tests for the !keep_existing tag."""

    def test_keep_existing_on_list(self, yaml_parser):
        """Test !keep_existing on a list."""
        data = """
        topics: !keep_existing
          - topicA
          - topicB
        """
        parsed_data = yaml_parser.load(data)
        assert isinstance(parsed_data["topics"], GitLabFormTagList)
        assert parsed_data["topics"].get_tag("keep_existing") is True
        assert "topicA" in parsed_data["topics"]
        assert "topicB" in parsed_data["topics"]

    def test_keep_existing_on_scalar(self, yaml_parser):
        """Test !keep_existing on scalar value."""
        data = """
        value: !keep_existing some_value
        """
        parsed_data = yaml_parser.load(data)
        assert isinstance(parsed_data["value"], GitLabFormTagScalar)
        assert parsed_data["value"].value == "some_value"
        assert parsed_data["value"].get_tag("keep_existing") is True


class TestIncludeTag:
    """Tests for the !include tag."""

    def test_include_external_file(self, yaml_parser):
        """Test !include with external file."""
        # Create a temporary YAML file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("key1: value1\nkey2: value2\n")
            temp_file = f.name

        try:
            data = f"""
            settings: !include {temp_file}
            """
            parsed_data = yaml_parser.load(data)
            assert "settings" in parsed_data
            assert parsed_data["settings"]["key1"] == "value1"
            assert parsed_data["settings"]["key2"] == "value2"
        finally:
            pathlib.Path(temp_file).unlink()

    def test_include_nonexistent_file(self, yaml_parser):
        """Test !include with nonexistent file raises error."""
        data = """
        settings: !include /nonexistent/file.yml
        """
        with pytest.raises(IOError, match="does not exist"):
            yaml_parser.load(data)

    def test_include_file_with_custom_tags(self, yaml_parser):
        """Test !include with file containing custom tags."""
        # Create a temporary YAML file with custom tags
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("project_settings: !inherit force\n")
            f.write("topics:\n")
            f.write("  - !delete topicA\n")
            f.write("  - topicB\n")
            temp_file = f.name

        try:
            data = f"""
            config: !include {temp_file}
            """
            parsed_data = yaml_parser.load(data)
            assert "config" in parsed_data
            assert isinstance(parsed_data["config"]["project_settings"], GitLabFormTagOrderedDict)
            assert parsed_data["config"]["project_settings"].get_tag("inherit") == "force"
            assert isinstance(parsed_data["config"]["topics"][0], GitLabFormTagScalar)
            assert parsed_data["config"]["topics"][0].get_tag("delete") is True
        finally:
            pathlib.Path(temp_file).unlink()


class TestCombinedTags:
    """Tests for combinations of tags."""

    def test_inherit_and_delete_in_same_config(self, yaml_parser):
        """Test using !inherit and !delete together."""
        data = """
        project_settings: !inherit force
        topics:
          - !delete topicA
          - topicB
        """
        parsed_data = yaml_parser.load(data)
        assert isinstance(parsed_data["project_settings"], GitLabFormTagOrderedDict)
        assert parsed_data["project_settings"].get_tag("inherit") == "force"
        assert isinstance(parsed_data["topics"][0], GitLabFormTagScalar)
        assert parsed_data["topics"][0].get_tag("delete") is True

    def test_enforce_and_keep_existing(self, yaml_parser):
        """Test using !enforce and !keep_existing together."""
        data = """
        settings:
          !enforce
          topics: !keep_existing
            - topicA
            - topicB
        """
        parsed_data = yaml_parser.load(data)
        assert isinstance(parsed_data["settings"], GitLabFormTagOrderedDict)
        assert parsed_data["settings"].get_tag("enforce") is True
        assert isinstance(parsed_data["settings"]["topics"], GitLabFormTagList)
        assert parsed_data["settings"]["topics"].get_tag("keep_existing") is True

    def test_complex_nested_tags(self, yaml_parser):
        """Test complex nested structure with multiple tags."""
        data = """
        projects_and_groups:
          group1/*:
            project_settings: !inherit force
            topics: !keep_existing
              - !delete oldTopic
              - newTopic
            members:
              !enforce
              users:
                user1:
                  access_level: maintainer
        """
        parsed_data = yaml_parser.load(data)
        group_config = parsed_data["projects_and_groups"]["group1/*"]

        # Check inherit tag
        assert isinstance(group_config["project_settings"], GitLabFormTagOrderedDict)
        assert group_config["project_settings"].get_tag("inherit") == "force"

        # Check keep_existing tag
        assert isinstance(group_config["topics"], GitLabFormTagList)
        assert group_config["topics"].get_tag("keep_existing") is True

        # Check delete tag within keep_existing list
        assert isinstance(group_config["topics"][0], GitLabFormTagScalar)
        assert group_config["topics"][0].get_tag("delete") is True

        # Check enforce tag
        assert isinstance(group_config["members"], GitLabFormTagOrderedDict)
        assert group_config["members"].get_tag("enforce") is True


class TestTagDataStructures:
    """Tests for the custom data structures."""

    def test_gitlabform_tag_ordered_dict(self):
        """Test GitLabFormTagOrderedDict functionality."""
        data = GitLabFormTagOrderedDict()
        data["key1"] = "value1"
        data.set_tag("inherit", "force")

        assert data["key1"] == "value1"
        assert data.has_tag("inherit")
        assert data.get_tag("inherit") == "force"
        assert not data.has_tag("nonexistent")
        assert data.get_tag("nonexistent", "default") == "default"
        assert data.get_tags() == {"inherit": "force"}

    def test_gitlabform_tag_scalar(self):
        """Test GitLabFormTagScalar functionality."""
        scalar = GitLabFormTagScalar("test_value", {"delete": True})

        assert scalar.value == "test_value"
        assert scalar.has_tag("delete")
        assert scalar.get_tag("delete") is True
        assert not scalar.has_tag("nonexistent")
        assert scalar.get_tag("nonexistent", "default") == "default"

    def test_gitlabform_tag_list(self):
        """Test GitLabFormTagList functionality."""
        tag_list = GitLabFormTagList(["item1", "item2"])
        tag_list.set_tag("keep_existing", True)

        assert len(tag_list) == 2
        assert tag_list[0] == "item1"
        assert tag_list.has_tag("keep_existing")
        assert tag_list.get_tag("keep_existing") is True
        assert not tag_list.has_tag("nonexistent")
        assert tag_list.get_tag("nonexistent", "default") == "default"
        assert tag_list.get_tags() == {"keep_existing": True}


class TestInheritEnum:
    """Tests for the InheritEnum."""

    def test_inherit_enum_values(self):
        """Test that all expected InheritEnum values are available."""
        assert InheritEnum.TRUE.value == "true"
        assert InheritEnum.FALSE.value == "false"
        assert InheritEnum.NEVER.value == "never"
        assert InheritEnum.ALWAYS.value == "always"
        assert InheritEnum.FORCE.value == "force"

    def test_inherit_enum_membership(self):
        """Test checking membership in InheritEnum."""
        valid_values = {e.value for e in InheritEnum}
        assert "true" in valid_values
        assert "false" in valid_values
        assert "never" in valid_values
        assert "always" in valid_values
        assert "force" in valid_values
        assert "invalid" not in valid_values
