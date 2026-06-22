import pytest

from gitlabform.configuration import Configuration


@pytest.fixture
def config_with_project_patterns():
    config_yaml = """
    ---
    projects_and_groups:
      "*":
        project_settings:
          common: true

      some_group/*:
        project_settings:
          group: true

      some_group/foo-*:
        project_settings:
          pattern: true

      some_group/foo-bar:
        project_settings:
          exact: true

      some_group/foo-bar-baz:
        project_settings:
          exact2: true
    """
    return Configuration(config_string=config_yaml)


@pytest.fixture
def config_with_pattern_specificity():
    config_yaml = """
    ---
    projects_and_groups:
      "*":
        project_settings:
          common: true

      some_group/*:
        project_settings:
          group: true

      some_group/foo-*:
        project_settings:
          prefix_pattern: true

      some_group/*bar:
        project_settings:
          suffix_pattern: true

      some_group/foo-*-baz:
        project_settings:
          mid_pattern: true
    """
    return Configuration(config_string=config_yaml)


@pytest.fixture
def config_with_skip_patterns():
    config_yaml = """
    ---
    projects_and_groups:
      "*":
        project_settings:
          common: true

    skip_groups:
      - group-skip-pattern-*/

    skip_projects:
      - group-old-*/skip-*
      - group-pattern/project-*
    """
    return Configuration(config_string=config_yaml)


class TestKeyType:
    def test_common(self):
        c = Configuration(config_string="projects_and_groups:\n  '*': {}\n")
        assert c._get_key_type("*") == "common"

    def test_group(self):
        c = Configuration(config_string="projects_and_groups:\n  group/*: {}\n")
        assert c._get_key_type("group/*") == "group"

    def test_project_pattern(self):
        c = Configuration(config_string="projects_and_groups:\n  group/foo-*: {}\n")
        assert c._get_key_type("group/foo-*") == "project_pattern"
        assert c._get_key_type("group/*foo*") == "project_pattern"

    def test_project(self):
        c = Configuration(config_string="projects_and_groups:\n  group/foo: {}\n")
        assert c._get_key_type("group/foo") == "project"


class TestMatchPattern:
    def test_match_simple_prefix(self):
        c = Configuration(config_string="projects_and_groups:\n  group/foo-*: {}\n")
        assert c._match_pattern("group/foo-*", "group/foo-bar") is True
        assert c._match_pattern("group/foo-*", "group/bar-baz") is False

    def test_match_anywhere(self):
        c = Configuration(config_string="projects_and_groups:\n  group/*bar*: {}\n")
        assert c._match_pattern("group/*bar*", "group/foobar") is True
        assert c._match_pattern("group/*bar*", "group/bar-baz") is True
        assert c._match_pattern("group/*bar*", "group/foo") is False

    def test_case_insensitive(self):
        c = Configuration(config_string="projects_and_groups:\n  group/FOO-*: {}\n")
        assert c._match_pattern("group/FOO-*", "group/foo-bar") is True


class TestGetProjects:
    def test_excludes_patterns(self, config_with_project_patterns):
        projects = config_with_project_patterns.get_projects()
        assert "some_group/foo-bar" in projects
        assert "some_group/foo-bar-baz" in projects
        assert "some_group/foo-*" not in projects
        assert "*" not in projects
        assert "some_group/*" not in projects

    def test_get_project_patterns(self, config_with_project_patterns):
        patterns = config_with_project_patterns.get_projects("project_pattern")
        assert "some_group/foo-*" in patterns
        assert "some_group/*" not in patterns
        assert "some_group/foo-bar" not in patterns


class TestGetGroups:
    def test_ignores_pattern_keys(self, config_with_project_patterns):
        groups = config_with_project_patterns.get_groups()
        assert "some_group" in groups
        assert "some_group/foo-*" not in groups


class TestSkipWithPatterns:
    def test_skip_project_pattern(self, config_with_skip_patterns):
        assert config_with_skip_patterns.is_project_skipped("group-pattern/project-abc") is True
        assert config_with_skip_patterns.is_project_skipped("group-pattern/project") is False
        assert config_with_skip_patterns.is_project_skipped("group-old-a/skip-x") is True
        assert config_with_skip_patterns.is_project_skipped("group-old-a/keep") is False

    def test_skip_group_fnmatch_patterns(self, config_with_skip_patterns):
        # verify that non-matching groups are not skipped
        assert config_with_skip_patterns.is_group_skipped("other-group") is False
        assert config_with_skip_patterns.is_group_skipped("group-old-a") is False
        assert config_with_skip_patterns.is_group_skipped("group-pattern") is False


class TestGetProjectConfig:
    def test_exact_project_wins_over_pattern(self, config_with_project_patterns):
        cfg = config_with_project_patterns._get_project_config("some_group/foo-bar")
        assert cfg == {"project_settings": {"exact": True}}

    def test_pattern_matches(self, config_with_project_patterns):
        cfg = config_with_project_patterns._get_project_config("some_group/foo-baz")
        assert cfg == {"project_settings": {"pattern": True}}

    def test_no_match_returns_empty(self, config_with_project_patterns):
        cfg = config_with_project_patterns._get_project_config("some_group/alpha-beta")
        assert cfg == {}

    def test_specificity_longer_prefix_wins(self, config_with_pattern_specificity):
        # some_group/foo-*-baz has longer prefix before first * than some_group/foo-*
        # both match "some_group/foo-x-baz", so longer prefix should win
        cfg = config_with_pattern_specificity._get_project_config("some_group/foo-x-baz")
        assert cfg == {"project_settings": {"mid_pattern": True}}

    def test_specificity_tie_goes_to_fewer_wildcards(self, config_with_pattern_specificity):
        # some_group/foo-* vs some_group/*bar:
        # "some_group/foo-bar" matches both.
        # foo-* prefix before first *: "some_group/foo-" len=15
        # *bar prefix before first *: "some_group/" len=11
        # longer prefix (foo-*) wins
        cfg = config_with_pattern_specificity._get_project_config("some_group/foo-bar")
        assert cfg == {"project_settings": {"prefix_pattern": True}}


class TestEffectiveConfigWithPatterns:
    def test_pattern_plus_group_plus_common(self, config_with_project_patterns):
        # some_group/foo-baz matches the pattern, not an exact project
        cfg = config_with_project_patterns.get_effective_config_for_project("some_group/foo-baz")
        assert cfg["project_settings"]["common"] is True
        assert cfg["project_settings"]["group"] is True
        assert cfg["project_settings"]["pattern"] is True
        assert "exact" not in cfg["project_settings"]
        assert "exact2" not in cfg["project_settings"]

    def test_exact_wins_over_pattern(self, config_with_project_patterns):
        cfg = config_with_project_patterns.get_effective_config_for_project("some_group/foo-bar")
        assert cfg["project_settings"]["exact"] is True
        assert "pattern" not in cfg["project_settings"]

    def test_only_group_plus_common_when_no_pattern(self, config_with_project_patterns):
        cfg = config_with_project_patterns.get_effective_config_for_project("some_group/zoo")
        assert cfg["project_settings"]["common"] is True
        assert cfg["project_settings"]["group"] is True
        assert "pattern" not in cfg["project_settings"]
