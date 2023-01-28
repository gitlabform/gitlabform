from tests.acceptance import (
    run_gitlabform,
)


def get_project_badges(project):
    badges = project.badges.list(iterator=True)
    return [badge for badge in badges if badge.kind == "project"]


class TestBadges:
    def test__badges_add(self, project):

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            badges:
              pipeline-status:
                name: "Project Badge"
                link_url: "https://gitlab.example.com/%{{project_path}}/-/commits/%{{default_branch}}/foo"
                image_url: "https://gitlab.example.com/%{{project_path}}/badges/%{{default_branch}}/pipeline.svg"
        """
        run_gitlabform(config, project)

        badges = get_project_badges(project)
        assert len(badges) == 1
        assert badges[0].name == "Project Badge"

    def test__badges_delete(self, project):

        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                badges:
                  pipeline-status:
                    name: "Project Badge"
                    link_url: "https://gitlab.example.com/%{{project_path}}/-/commits/%{{default_branch}}/foo"
                    image_url: "https://gitlab.example.com/%{{project_path}}/badges/%{{default_branch}}/pipeline.svg"
            """
        run_gitlabform(config, project)

        badges = get_project_badges(project)
        assert len(badges) == 1
        assert badges[0].name == "Project Badge"

        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                badges:
                  pipeline-status:
                    name: "Project Badge"
                    delete: true
            """
        run_gitlabform(config, project)

        badges = get_project_badges(project)
        assert len(badges) == 0

    def test__badges_update(self, project):

        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                badges:
                  pipeline-status:
                    name: "Project Badge"
                    link_url: "https://gitlab.example.com/foo"
                    image_url: "https://gitlab.example.com/pipeline.svg"
            """
        run_gitlabform(config, project)

        badges = get_project_badges(project)
        assert len(badges) == 1
        assert badges[0].link_url.endswith("foo")

        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                badges:
                  pipeline-status:
                    name: "Project Badge"
                    link_url: "https://gitlab.example.com/bar"
                    image_url: "https://gitlab.example.com/pipeline.svg"
            """
        run_gitlabform(config, project)

        badges = get_project_badges(project)
        assert len(badges) == 1
        assert badges[0].link_url.endswith("bar")

    def test__badges_update_choose_the_right_one(self, project):

        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                badges:
                  pipeline-status:
                    name: "Project Badge"
                    link_url: "https://gitlab.example.com/first"
                    image_url: "https://gitlab.example.com/first"
                  another:
                    name: "Project Badge 2"
                    link_url: "https://gitlab.example.com/second"
                    image_url: "https://gitlab.example.com/second" 
            """
        run_gitlabform(config, project)

        badges = get_project_badges(project)
        assert len(badges) == 2

        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                badges:
                  a_different_key:
                    name: "Project Badge 2"
                    link_url: "https://gitlab.example.com/foobar"
                    image_url: "https://gitlab.example.com/foobar"
                  and_also_different_than_before:
                    name: "Project Badge"
                    delete: true
            """
        run_gitlabform(config, project)

        badges = get_project_badges(project)
        assert len(badges) == 1

        for badge in badges:
            if badge.name == "Project Badge 2":
                assert badge.link_url.endswith("foobar")
                assert badge.image_url.endswith("foobar")
            else:
                assert not badge.link_url.endswith("foobar")
                assert not badge.image_url.endswith("foobar")

    def test__badges_enforce(self, project_for_function):

        config = f"""
            projects_and_groups:
              {project_for_function.path_with_namespace}:
                badges:
                  pipeline-status:
                    name: "Project Badge"
                    link_url: "https://gitlab.example.com/first"
                    image_url: "https://gitlab.example.com/first"
                  another:
                    name: "Project Badge 2"
                    link_url: "https://gitlab.example.com/second"
                    image_url: "https://gitlab.example.com/second" 
            """
        run_gitlabform(config, project_for_function.path_with_namespace)

        badges = get_project_badges(project_for_function)
        assert len(badges) == 2

        config2 = f"""
            projects_and_groups:
              {project_for_function.path_with_namespace}:
                badges:
                  another:
                    name: "Project Badge 2"
                    link_url: "https://gitlab.example.com/foobar"
                    image_url: "https://gitlab.example.com/foobar"
                  enforce: true
            """
        run_gitlabform(config2, project_for_function.path_with_namespace)

        badges = get_project_badges(project_for_function)
        assert len(badges) == 1
