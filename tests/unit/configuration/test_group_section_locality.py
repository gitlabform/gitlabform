from gitlabform.configuration import Configuration


def test__has_group_section_defined_locally__returns_true_for_exact_subgroup_key():
    configuration = Configuration(config_string="""
        ---
        projects_and_groups:
          some_group/*:
            group_members:
              users: {}
          some_group/subgroup/*:
            group_settings:
              visibility: private
        """)

    assert configuration.has_group_section_defined_locally("some_group", "group_members") is True
    assert configuration.has_group_section_defined_locally("some_group/subgroup", "group_members") is False
    assert configuration.has_group_section_defined_locally("some_group/subgroup", "group_settings") is True
