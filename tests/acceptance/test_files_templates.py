from tests.acceptance import run_gitlabform, DEFAULT_README


class TestFilesTemplates:
    def test__default_variables(self, gitlab, group_and_project):

        config = (
            """
        projects_and_groups:
          """
            + group_and_project
            + """:
            files:
              "README.md":
                overwrite: true
                branches: all
                content: |
                  This is a text that contains the default variables: {{ group }}/{{ project }}
        """
        )

        run_gitlabform(config, group_and_project)

        file_content = gitlab.get_file(group_and_project, "main", "README.md")
        # TODO: the file_content should actually end with a new line, as this is how the original content above ends
        assert (
            file_content
            == f"This is a text that contains the default variables: "
            + group_and_project
        )

    def test__custom_variables(self, gitlab, group_and_project):

        config = (
            """
        projects_and_groups:
          """
            + group_and_project
            + """:
            files:
              "README.md":
                overwrite: true
                branches: all
                jinja_env:
                  foo: "fooz"
                  bar: "barz"
                content: |
                  This is a text that contains custom variables: {{ foo }}, {{ bar }}
        """
        )

        run_gitlabform(config, group_and_project)

        file_content = gitlab.get_file(group_and_project, "main", "README.md")
        # TODO: the file_content should actually end with a new line, as this is how the original content above ends
        assert (
            file_content == "This is a text that contains custom variables: fooz, barz"
        )

    def test__disabled_templating(self, gitlab, group_and_project):

        config = (
            """
        projects_and_groups:
          """
            + group_and_project
            + """:
            files:
              "README.md":
                overwrite: true
                branches: all
                template: no
                content: |
                  This is a text containing literals: {{ group }}/{{ project }}
        """
        )

        run_gitlabform(config, group_and_project)

        file_content = gitlab.get_file(group_and_project, "main", "README.md")
        assert (
            file_content
            == "This is a text containing literals: {{ group }}/{{ project }}\n"
        )
