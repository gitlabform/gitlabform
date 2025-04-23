from tests.acceptance import run_gitlabform


class TestGroupLabels:
    def test__can_add_a_label_to_group(self, gl, group_for_function):
        group = gl.groups.get(group_for_function.id)
        labels = group.labels.list()
        assert len(labels) == 0

        config_for_labels = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_labels:
              test_label:
                color: red
                description: this is a label
        """

        run_gitlabform(config_for_labels, group_for_function)

        updated_group = gl.groups.get(group.id)
        updated_labels = updated_group.labels.list()
        assert len(updated_labels) == 1

        updated_label = updated_labels[0]
        assert updated_label.name == "test_label"
        assert updated_label.description == "this is a label"

        # text color gets converted to HexCode by GitLab ie red -> #FF0000
        assert updated_label.color == "#FF0000"

    def test__removes_existing_label_when_enforce_is_true(self, gl, group_for_function):
        group = gl.groups.get(group_for_function.id)
        group.labels.create({"name": "delete_this", "color": "red"})
        labels = group.labels.list()
        assert len(labels) == 1

        config_for_labels = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_labels:
              enforce: true
              test_label:
                color: red
                description: this is a label
        """

        run_gitlabform(config_for_labels, group_for_function)

        updated_group = gl.groups.get(group.id)
        updated_labels = updated_group.labels.list()
        assert len(updated_labels) == 1

        updated_label = updated_labels[0]
        assert updated_label.name == "test_label"
        assert updated_label.description == "this is a label"

        # text color gets converted to HexCode by GitLab ie red -> #FF0000
        assert updated_label.color == "#FF0000"

    def test__leaves_existing_label_when_enforce_is_false(self, gl, group_for_function):
        group = gl.groups.get(group_for_function.id)
        group.labels.create({"name": "delete_this", "color": "red"})
        labels = group.labels.list()
        assert len(labels) == 1

        config_for_labels = f"""
        projects_and_groups:
          {group.full_path}/*:
            group_labels:
              test_label:
                color: red
                description: this is a label
        """

        run_gitlabform(config_for_labels, group_for_function)

        updated_group = gl.groups.get(group.id)
        updated_labels = updated_group.labels.list()
        assert len(updated_labels) == 2

        existing_label = updated_labels[0]
        assert existing_label.name == "delete_this"
        assert existing_label.color == "#FF0000"

        new_label = updated_labels[1]
        assert new_label.name == "test_label"
        assert new_label.description == "this is a label"

        # text color gets converted to HexCode by GitLab ie red -> #FF0000
        assert new_label.color == "#FF0000"

    def test__updates_existing_label(self, gl, group_for_function):
        group = gl.groups.get(group_for_function.id)
        created_label = group.labels.create({"name": "update_this", "color": "red", "description": "hello world"})

        labels = group.labels.list()
        assert len(labels) == 1

        config_for_labels = f"""
          projects_and_groups:
            {group.full_path}/*:
              group_labels:
                update_this:
                  color: blue
                  description: this is a label
          """

        run_gitlabform(config_for_labels, group_for_function)

        updated_group = gl.groups.get(group.id)
        updated_labels = updated_group.labels.list()
        assert len(updated_labels) == 1

        new_label = updated_labels[0]
        assert new_label.name == "update_this"
        assert new_label.description == "this is a label"

        # text color gets converted to HexCode by GitLab ie blue -> #0000FF
        assert new_label.color == "#0000FF"

        # validate same id is being used
        assert created_label.id == new_label.id

    def test__does_not_try_to_remove_existing_label_on_parent_group_when_enforce_is_true(
        self, gl, group_for_function, subgroup_for_function
    ):
        parent_group = gl.groups.get(group_for_function.id)
        parent_group.labels.create({"name": "do_not_delete_this", "color": "red"})
        labels = parent_group.labels.list()
        assert len(labels) == 1

        config_for_labels = f"""
        projects_and_groups:
          {subgroup_for_function.full_path}/*:
            group_labels:
              enforce: true
              test_label:
                color: red
                description: this is a label
        """

        run_gitlabform(config_for_labels, group_for_function)

        updated_sub_group = gl.groups.get(subgroup_for_function.id)
        updated_labels = updated_sub_group.labels.list()
        assert len(updated_labels) == 2

        parent_label = updated_labels[0]
        assert parent_label.name == "do_not_delete_this"

        updated_label = updated_labels[1]
        assert updated_label.name == "test_label"
        assert updated_label.description == "this is a label"

        # text color gets converted to HexCode by GitLab ie red -> #FF0000
        assert updated_label.color == "#FF0000"
