from gitlabform.gitlab import AccessLevel


def test_group_access_levels_type():
    group_access_levels = AccessLevel.group_levels()
    assert type(group_access_levels[0]) is int


def test_group_access_levels():
    group_access_levels = AccessLevel.group_levels()
    assert AccessLevel.NO_ACCESS.value in group_access_levels
    assert AccessLevel.OWNER.value in group_access_levels
    assert AccessLevel.ADMIN.value not in group_access_levels


def test_sortability_of_access_levels():
    sorted_group_access_levels = sorted(AccessLevel)
    assert sorted_group_access_levels[0] == AccessLevel.NO_ACCESS.value
    assert sorted_group_access_levels[-1] == AccessLevel.ADMIN.value
