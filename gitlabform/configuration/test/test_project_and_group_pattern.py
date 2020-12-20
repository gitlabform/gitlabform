from gitlabform.configuration.project_path import ProjectPath


def test_all_projects_pattern_for_project():
    pattern = ProjectPath("*")

    assert pattern.matches_path("foo") is True


def test_all_projects_pattern_for_group():
    pattern = ProjectPath("*")

    assert pattern.matches_path("foo-group/bar-subgroup") is True


def test_all_personal_projects_pattern_with_regex():
    pattern = ProjectPath("<all-users>~foo*")

    assert pattern.is_all_personal_projects_pattern() is False


def test__all_personal_projects_pattern():
    pattern = ProjectPath("<all-users>")

    assert pattern.is_all_personal_projects_pattern() is True


def test__project_with_exact_path_is_matched():
    pattern = ProjectPath("foo/bar")

    assert pattern.matches_path("foo/bar") is True


def test__project_with_group_in_pattern_is_matched():
    pattern = ProjectPath("foo")

    assert pattern.matches_path("foo/bar") is True
