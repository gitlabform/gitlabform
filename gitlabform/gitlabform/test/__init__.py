from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import NotFoundException, UnexpectedResponseException

CONFIG = """
gitlab:
  # GITLAB_URL and GITLAB_TOKEN should be in the env variables
  api_version: 4
    """

GROUP_NAME = "gitlabform_tests_group"

DEVELOPER_ACCESS = 30
OWNER_ACCESS = 50

gl = GitLab(config_string=CONFIG)


def get_gitlab():
    return gl


def create_group(group_name):
    try:
        gl.get_group(group_name)
    except NotFoundException:
        gl.create_group(group_name, group_name)


def create_project_in_group(group_name, project_name):
    try:
        gl.get_project(group_name + "/" + project_name)
    except NotFoundException:
        group = gl.get_group(group_name)
        gl.create_project(project_name, project_name, group["id"], "main")


def create_users_in_project(user_base_name, no_of_users, project_and_group):
    for user_no in range(1, no_of_users + 1):
        username = user_base_name + str(user_no)
        try:
            gl.get_user_by_name(username)
        except NotFoundException:
            gl.create_user(
                username + "@example.com", username + " Example", username, "password"
            )

        try:
            gl.add_member_to_project(project_and_group, username, DEVELOPER_ACCESS)
        except UnexpectedResponseException:
            # this is fine - user is already in the project
            pass


def create_users(user_base_name, no_of_users):
    for user_no in range(1, no_of_users + 1):
        username = user_base_name + str(user_no)
        try:
            gl.get_user_by_name(username)
        except NotFoundException:
            gl.create_user(
                username + "@example.com", username + " Example", username, "password"
            )


def delete_users(user_base_name, no_of_users):
    for user_no in range(1, no_of_users + 1):
        username = user_base_name + str(user_no)
        gl.delete_user(username)


def add_users_to_group(group_name, usernames, access_level=DEVELOPER_ACCESS):
    for username in usernames:
        try:
            gl.add_member_to_group(group_name, username, access_level)
        except UnexpectedResponseException:
            # this is fine - user is already in the group
            pass


def remove_users_from_group(group_name, usernames):
    for username in usernames:
        try:
            gl.remove_member_from_group(group_name, username)
        except NotFoundException:
            # this is fine - user is removed from group
            pass


def create_readme_in_project(project_and_group):
    try:
        gl.get_file(project_and_group, "main", "README.md")
        gl.set_file(
            project_and_group,
            "main",
            "README.md",
            "Hello World!",
            "Restore original content",
        )
    except:
        gl.add_file(
            project_and_group, "main", "README.md", "Hello World!", "Create README"
        )


def delete_variables_from_group(group_name, variables):
    for variable in variables:
        try:
            gl.delete_group_secret_variable(group_name, variable)
        except NotFoundException:
            # this is fine - variable is removed from group
            pass


def delete_pipeline_schedules_from_project(project_and_group):
    schedules = gl.get_all_pipeline_schedules(project_and_group)
    for schedule in schedules:
        gl.delete_pipeline_schedule(project_and_group, schedule["id"])
