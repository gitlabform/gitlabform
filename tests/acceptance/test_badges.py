from tests.acceptance import (
    run_gitlabform,
)


class TestBadges:
    def test__badges_add(self, gitlab, group_and_project):

        config = f"""
        projects_and_groups:
          {group_and_project}:
            badges:
              pipeline-status:
                name: "Project Badge"
                link_url: "https://gitlab.example.com/%{{project_path}}/-/commits/%{{default_branch}}/foo"
                image_url: "https://gitlab.example.com/%{{project_path}}/badges/%{{default_branch}}/pipeline.svg"
        """
        run_gitlabform(config, group_and_project)

        badges = gitlab.get_project_badges(group_and_project)
        assert len(badges) == 1
        assert badges[0]["name"] == "Project Badge"

    def test__badges_delete(self, gitlab, group_and_project):

        config = f"""
            projects_and_groups:
              {group_and_project}:
                badges:
                  pipeline-status:
                    name: "Project Badge"
                    link_url: "https://gitlab.example.com/%{{project_path}}/-/commits/%{{default_branch}}/foo"
                    image_url: "https://gitlab.example.com/%{{project_path}}/badges/%{{default_branch}}/pipeline.svg"
            """
        run_gitlabform(config, group_and_project)

        badges = gitlab.get_project_badges(group_and_project)
        assert len(badges) == 1
        assert badges[0]["name"] == "Project Badge"

        config = f"""
            projects_and_groups:
              {group_and_project}:
                badges:
                  pipeline-status:
                    name: "Project Badge"
                    delete: true
            """
        run_gitlabform(config, group_and_project)

        badges = gitlab.get_project_badges(group_and_project)
        assert len(badges) == 0

    def test__badges_update(self, gitlab, group_and_project):

        config = f"""
            projects_and_groups:
              {group_and_project}:
                badges:
                  pipeline-status:
                    name: "Project Badge"
                    link_url: "https://gitlab.example.com/foo"
                    image_url: "https://gitlab.example.com/pipeline.svg"
            """
        run_gitlabform(config, group_and_project)

        badges = gitlab.get_project_badges(group_and_project)
        assert len(badges) == 1
        assert badges[0]["link_url"].endswith("foo")

        config = f"""
            projects_and_groups:
              {group_and_project}:
                badges:
                  pipeline-status:
                    name: "Project Badge"
                    link_url: "https://gitlab.example.com/bar"
                    image_url: "https://gitlab.example.com/pipeline.svg"
            """
        run_gitlabform(config, group_and_project)

        badges = gitlab.get_project_badges(group_and_project)
        assert len(badges) == 1
        assert badges[0]["link_url"].endswith("bar")

    def test__badges_update_choose_the_right_one(self, gitlab, group_and_project):

        config = f"""
            projects_and_groups:
              {group_and_project}:
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
        run_gitlabform(config, group_and_project)

        badges = gitlab.get_project_badges(group_and_project)
        assert len(badges) == 2

        config = f"""
            projects_and_groups:
              {group_and_project}:
                badges:
                  a_different_key:
                    name: "Project Badge 2"
                    link_url: "https://gitlab.example.com/foobar"
                    image_url: "https://gitlab.example.com/foobar"
                  and_also_different_than_before:
                    name: "Project Badge"
                    delete: true
            """
        run_gitlabform(config, group_and_project)

        badges = gitlab.get_project_badges(group_and_project)
        assert len(badges) == 1

        for badge in badges:
            if badge["name"] == "Project Badge 2":
                assert badge["link_url"].endswith("foobar")
                assert badge["image_url"].endswith("foobar")
            else:
                assert not badge["link_url"].endswith("foobar")
                assert not badge["image_url"].endswith("foobar")
