from tests.acceptance import run_gitlabform


class TestProjectLabels:
    def test__can_add_a_label_to_project(self, gl, project_for_function):
        project = gl.projects.get(project_for_function.id)
        labels = project.labels.list()
        assert len(labels) == 0

        config_for_labels = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            labels:
              test_label:
                color: red
                description: this is a label
                priority: 1
        """

        run_gitlabform(config_for_labels, project_for_function)

        updated_project = gl.projects.get(project.id)
        updated_project = gl.projects.get(project.id)
        updated_labels = updated_project.labels.list()
        assert len(updated_labels) == 1

        updated_label = updated_labels[0]
        assert updated_label.name == "test_label"
        assert updated_label.description == "this is a label"
        assert updated_label.priority == 1

        # text color gets converted to HexCode by GitLab ie red -> #FF0000
        assert updated_label.color == "#FF0000"

    def test__removes_existing_label_when_enforce_is_true(
        self, gl, project_for_function
    ):
        project = gl.projects.get(project_for_function.id)
        project.labels.create({"name": "delete_this", "color": "red"})
        labels = project.labels.list()
        assert len(labels) == 1

        config_for_labels = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            labels:
              enforce: true
              test_label:
                color: red
                description: this is a label
                priority: 1
        """

        run_gitlabform(config_for_labels, project_for_function)

        updated_project = gl.projects.get(project.id)
        updated_labels = updated_project.labels.list()
        assert len(updated_labels) == 1

        updated_label = updated_labels[0]
        assert updated_label.name == "test_label"
        assert updated_label.description == "this is a label"
        assert updated_label.priority == 1

        # text color gets converted to HexCode by GitLab ie red -> #FF0000
        assert updated_label.color == "#FF0000"

    def test__leaves_existing_label_when_enforce_is_false(
        self, gl, project_for_function
    ):
        project = gl.projects.get(project_for_function.id)
        project.labels.create({"name": "delete_this", "color": "red"})
        labels = project.labels.list()
        assert len(labels) == 1

        config_for_labels = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            labels:
              test_label:
                color: red
                description: this is a label
                priority: 1
        """

        run_gitlabform(config_for_labels, project_for_function)

        updated_project = gl.projects.get(project.id)
        updated_labels = updated_project.labels.list()
        assert len(updated_labels) == 2

        existing_label = updated_labels[0]
        assert existing_label.name == "delete_this"
        assert existing_label.color == "#FF0000"

        new_label = updated_labels[1]
        assert new_label.name == "test_label"
        assert new_label.description == "this is a label"
        assert new_label.priority == 1

        # text color gets converted to HexCode by GitLab ie red -> #FF0000
        assert new_label.color == "#FF0000"

    def test__updates_existing_label(self, gl, project_for_function):
        project = gl.projects.get(project_for_function.id)
        created_label = project.labels.create(
            {
                "name": "update_this",
                "color": "red",
                "priority": 1,
            }
        )

        labels = project.labels.list()
        assert len(labels) == 1

        config_for_labels = f"""
          projects_and_groups:
            {project.path_with_namespace}:
              labels:
                update_this:
                  color: blue
                  description: this is a label
                  priority: 2
          """

        run_gitlabform(config_for_labels, project_for_function)

        updated_project = gl.projects.get(project.id)
        updated_labels = updated_project.labels.list()
        assert len(updated_labels) == 1

        new_label = updated_labels[0]
        assert new_label.name == "update_this"
        assert new_label.description == "this is a label"
        assert new_label.priority == 2

        # text color gets converted to HexCode by GitLab ie blue -> #0000FF
        assert new_label.color == "#0000FF"

        # validate same id is being used
        assert created_label.id == new_label.id
