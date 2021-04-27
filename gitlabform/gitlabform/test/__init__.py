import os
import re
import textwrap

import pytest
from xkcdpass import xkcd_password as xp

from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import NotFoundException, UnexpectedResponseException
from gitlabform.gitlabform import GitLabForm

CONFIG = """
gitlab:
  # GITLAB_URL and GITLAB_TOKEN should be in the env variables
  api_version: 4
"""

# automate reading files created by run_gitlab_in_docker.sh to run tests in PyCharm / IntelliJ
# (workaround for lack of this feature: https://youtrack.jetbrains.com/issue/PY-5543 )

env_vars_and_file_paths = {
    "GITLAB_URL": "gitlab_url.txt",
    "GITLAB_TOKEN": "gitlab_token.txt",
}

for env_var, file_path in env_vars_and_file_paths.items():
    if env_var not in os.environ:
        print(f"{env_var} not set - trying to read it from {file_path} ...")
        if os.path.isfile(file_path):
            try:
                with open(file_path, "r") as file:
                    os.environ[env_var] = file.read().replace("\n", "")
                    print(f"{env_var} set!")
            except Exception as e:
                print(f"Failed to read {file_path}: {e}")
        else:
            print(f"{file_path} doesn't exist.")

GROUP_NAME_PREFIX = "gitlabform_tests_group"

DEVELOPER_ACCESS = 30
OWNER_ACCESS = 50

gl = GitLab(config_string=CONFIG)


def get_group_name(test_type):
    random_suffix = get_random_suffix(test_type, True)
    return f"{GROUP_NAME_PREFIX}__{test_type}__{random_suffix}"


def get_project_name(test_type):
    random_suffix = get_random_suffix(test_type, True)
    return f"{test_type}_project__{random_suffix}"


def get_group_and_project_names(test_type, unique):
    random_suffix = get_random_suffix(test_type, unique)
    group_name = f"{GROUP_NAME_PREFIX}__{random_suffix}"
    project_name = f"{test_type}_project__{random_suffix}"
    group_and_project_name = f"{group_name}/{project_name}"
    return group_name, project_name, group_and_project_name


random_suffixes_per_type = {}
word_file = xp.locate_wordfile()
my_words = xp.generate_wordlist(wordfile=word_file, min_length=5, max_length=8)


def get_random_suffix(test_type, unique):
    if unique:
        return xp.generate_xkcdpassword(wordlist=my_words, numwords=2, delimiter="_")
    else:
        if test_type in random_suffixes_per_type:
            return random_suffixes_per_type[test_type]
        else:
            random_suffix = xp.generate_xkcdpassword(
                wordlist=my_words, numwords=2, delimiter="_"
            )
            random_suffixes_per_type[test_type] = random_suffix
            return random_suffix


def get_gitlab():
    return gl


def create_group(group_name):
    gl.create_group(group_name, group_name)


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
        "Hello World!",
        "Create README",
    )


def delete_group_and_project(group_name, project_name):
    gl.delete_project(f"{group_name}/{project_name}")
    gl.delete_group(group_name)


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
    # we don't want to repeat ourselves in the tests, so prefix the configs with this mandatory part here
    config_prefix = "gitlab:\n  api_version: 4\n\n"

    # f-strings with """ used as configs have the disadvantage of having indentation in them - let's remove it here
    config = textwrap.dedent(config)

    config = config_prefix + config

    gf = GitLabForm(
        config_string=config,
        project_or_group=group_and_project,
    )
    gf.main()
