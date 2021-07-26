import os
import textwrap

from xkcdpass import xkcd_password as xp

from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import NotFoundException, UnexpectedResponseException
from gitlabform import GitLabForm

CONFIG = """
config_version: 2
"""

DEFAULT_README = "Default README content."

# automate reading files created by run_gitlab_in_docker.sh to run tests in PyCharm / IntelliJ
# (workaround for lack of this feature: https://youtrack.jetbrains.com/issue/PY-5543 )

env_vars_and_file_paths = {
    "GITLAB_URL": ["gitlab_url.txt", "../../../gitlab_url.txt"],
    "GITLAB_TOKEN": ["gitlab_token.txt", "../../../gitlab_token.txt"],
}

for env_var, file_paths in env_vars_and_file_paths.items():
    if env_var not in os.environ:
        print(f"{env_var} not set - trying to read it from {file_paths} ...")
        for file_path in file_paths:
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as file:
                        os.environ[env_var] = file.read().replace("\n", "")
                        print(f"{env_var} set!")
                except Exception as e:
                    print(f"Failed to read {file_path}: {e}")
            else:
                print(f"{file_path} doesn't exist.")

DEVELOPER_ACCESS = 30
MAINTAINER_ACCESS = 40
OWNER_ACCESS = 50

gl = GitLab(config_string=CONFIG)


def get_random_name():
    random_suffix = get_random_suffix()
    return f"gitlabform__{random_suffix}"


word_file = xp.locate_wordfile()
my_words = xp.generate_wordlist(wordfile=word_file, min_length=5, max_length=8)


def get_random_suffix():
    return xp.generate_xkcdpassword(wordlist=my_words, numwords=2, delimiter="_")


def get_gitlab():
    return gl


def create_group(group_name, parent_id=None):
    gl.create_group(group_name, group_name, parent_id)


def create_groups(group_base_name, no_of_groups):
    groups = []
    for group_no in range(1, no_of_groups + 1):
        group_name = group_base_name + str(group_no)
        try:
            gl.get_group_case_insensitive(group_name)
        except NotFoundException:
            gl.create_group(group_name, group_name)
        groups.append(group_name)
    return groups


def delete_groups(group_base_name, no_of_groups):
    for group_no in range(1, no_of_groups + 1):
        group_name = group_base_name + str(group_no)
        gl.delete_group(group_name)


def create_project(group_name, project_name):
    group = gl.get_group(group_name)
    gl.create_project(
        project_name,
        project_name,
        group["id"],
        default_branch="main",
        wait_if_still_being_deleted=True,
    )

    gl.add_file(
        f"{group_name}/{project_name}",
        "main",
        "README.md",
        DEFAULT_README,
        "Create README",
    )


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
    users = []
    for user_no in range(1, no_of_users + 1):
        username = user_base_name + str(user_no)
        try:
            gl.get_user_by_name(username)
        except NotFoundException:
            gl.create_user(
                username + "@example.com", username + " Example", username, "password"
            )
        users.append(username)
    return users


def delete_users(user_base_name, no_of_users):
    for user_no in range(1, no_of_users + 1):
        username = user_base_name + str(user_no)
        gl.delete_user(username)


def remove_users_from_project(user_base_name, no_of_users, project_and_group):
    for user_no in range(1, no_of_users + 1):
        username = user_base_name + str(user_no)
        gl.remove_member_from_project(project_and_group, username)


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


def run_gitlabform(config, group_and_project):
    # f-strings with """ used as configs have the disadvantage of having indentation in them - let's remove it here
    config = textwrap.dedent(config)

    # we don't want to repeat ourselves in the tests, so prefix the configs with this mandatory part here
    config = CONFIG + config

    gf = GitLabForm(
        config_string=config,
        project_or_group=group_and_project,
    )
    gf.main()
