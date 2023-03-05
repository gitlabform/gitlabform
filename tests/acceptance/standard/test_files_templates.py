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
    def test__default_variables(self, gitlab, group_and_project):
        config = f"""
        projects_and_groups:
          {group_and_project}:
            files:
              "README.md":
                overwrite: true
                branches: all
                content: |
                  This is a text that contains the default variables: {{{{ group }}}}/{{{{ project }}}}
        """

        run_gitlabform(config, group_and_project)

        file_content = gitlab.get_file(group_and_project, "main", "README.md")
        assert (
            file_content
            == f"This is a text that contains the default variables: {group_and_project}\n"
        )

    def test__custom_variables(self, gitlab, group_and_project):
        config = f"""
        projects_and_groups:
          {group_and_project}:
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

        run_gitlabform(config, group_and_project)

        file_content = gitlab.get_file(group_and_project, "main", "README.md")
        assert (
            file_content
            == "This is a text that contains custom variables: fooz, barz\n"
        )

    def test__trailing_new_lines(self, gitlab, group_and_project, file3):
        set_file_chinese_characters = f"""
        projects_and_groups:
          {group_and_project}:
            files:
              "README.md":
                overwrite: true
                branches: all
                file: file3.txt
        """

        run_gitlabform(set_file_chinese_characters, group_and_project)

        file_content = gitlab.get_file(group_and_project, "main", "README.md")
        assert file_content == f"{group_and_project}\n\n"

    def test__disabled_templating(self, gitlab, group_and_project):
        config = f"""
        projects_and_groups:
          {group_and_project}:
            files:
              "README.md":
                overwrite: true
                branches: all
                template: no
                content: |
                  This is a text containing literals: {{{{ group }}}}/{{{{ project }}}}
        """

        run_gitlabform(config, group_and_project)

        file_content = gitlab.get_file(group_and_project, "main", "README.md")
        assert (
            file_content
            == "This is a text containing literals: {{ group }}/{{ project }}\n"
        )
