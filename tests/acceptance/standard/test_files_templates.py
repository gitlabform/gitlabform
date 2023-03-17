import os
import pytest

from tests.acceptance import run_gitlabform


@pytest.fixture(scope="class")
def file3(request):
    f = open("file3.txt", "a")
    f.write("{{ group }}/{{ project }}\n\n")
    f.close()

    def fin():
        os.remove("file3.txt")

    request.addfinalizer(fin)


class TestFilesTemplates:
    def test__default_variables(self, project):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            files:
              "README.md":
                overwrite: true
                branches: all
                content: |
                  This is a text that contains the default variables: {{{{ group }}}}/{{{{ project }}}}
        """

        run_gitlabform(config, project)

        project_file = project.files.get(ref="main", file_path="README.md")
        assert (
            project_file.decode().decode("utf-8")
            == f"This is a text that contains the default variables: {project.path_with_namespace}\n"
        )

    def test__custom_variables(self, project):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            files:
              "README.md":
                overwrite: true
                branches: all
                jinja_env:
                  foo: "fooz"
                  bar: "barz"
                content: |
                  This is a text that contains custom variables: {{{{ foo }}}}, {{{{ bar }}}}
        """

        run_gitlabform(config, project)

        project_file = project.files.get(ref="main", file_path="README.md")
        assert (
            project_file.decode().decode("utf-8")
            == "This is a text that contains custom variables: fooz, barz\n"
        )

    def test__trailing_new_lines(self, project, file3):
        set_file_chinese_characters = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            files:
              "README.md":
                overwrite: true
                branches: all
                file: file3.txt
        """

        run_gitlabform(set_file_chinese_characters, project.path_with_namespace)

        project_file = project.files.get(ref="main", file_path="README.md")
        assert (
            project_file.decode().decode("utf-8")
            == f"{project.path_with_namespace}\n\n"
        )

    def test__disabled_templating(self, project):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            files:
              "README.md":
                overwrite: true
                branches: all
                template: no
                content: |
                  This is a text containing literals: {{{{ group }}}}/{{{{ project }}}}
        """

        run_gitlabform(config, project.path_with_namespace)

        project_file = project.files.get(ref="main", file_path="README.md")
        assert (
            project_file.decode().decode("utf-8")
            == "This is a text containing literals: {{ group }}/{{ project }}\n"
        )
