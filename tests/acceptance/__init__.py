import os
import textwrap

from xkcdpass import xkcd_password as xp

from gitlabform import GitLabForm
from gitlabform.gitlab import GitLab, AccessLevel
from gitlabform.gitlab.core import NotFoundException, UnexpectedResponseException

CONFIG = """
config_version: 3
"""

DEFAULT_README = "Default README content."

# automate reading files created by run_gitlab_in_docker.sh to run tests in PyCharm / IntelliJ
# (workaround for lack of this feature: https://youtrack.jetbrains.com/issue/PY-5543 )

env_vars_to_files = {
    "GITLAB_URL": "gitlab_url.txt",
    "GITLAB_TOKEN": "gitlab_token.txt",
}

for env_var in env_vars_to_files.keys():
    if env_var not in os.environ:
        print(f"{env_var} not set - trying to read it from a file...")
        for up_dir_level in range(0, 4):
            file_path = (up_dir_level * "../") + env_vars_to_files[env_var]
            print(f"Trying to read {file_path} ...")
            if os.path.isfile(file_path):
                try:
                    with open(file_path) as file:
                        os.environ[env_var] = file.read().strip()
                        print(f"{env_var} set!")
                        break
                except Exception as e:
                    print(f"Failed to read {file_path}: {e}")
            else:
                print(f"{file_path} doesn't exist.")

gl = GitLab(config_string=CONFIG)


def get_random_name(entity: str) -> str:
    random_suffix = get_random_suffix()
    return f"gitlabform_{entity}_{random_suffix}"


word_file = xp.locate_wordfile()
my_words = xp.generate_wordlist(wordfile=word_file, min_length=5, max_length=8)


def get_random_suffix():
    return xp.generate_xkcdpassword(wordlist=my_words, numwords=1, delimiter="_")


def get_random_password():
    return xp.generate_xkcdpassword(wordlist=my_words, numwords=3, delimiter="_")


def get_gitlab():
    return gl


def create_group(group_name, parent_id=None):
    gl.create_group(group_name, group_name, parent_id=parent_id, visibility="internal")


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


def create_users(user_base_name, no_of_users):
    users = []
    for user_no in range(1, no_of_users + 1):
        username = user_base_name + str(user_no)
        try:
            gl.get_user_by_name(username)
        except NotFoundException:
            gl.create_user(
                username + "@example.com",
                username + " Example",
                username,
                get_random_password(),
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


def add_users_to_group(group_name, usernames, access_level=AccessLevel.DEVELOPER.value):
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
            gl.delete_group_variable(group_name, variable)
        except NotFoundException:
            # this is fine - variable is removed from group
            pass


def delete_pipeline_schedules_from_project(project_and_group):
    schedules = gl.get_all_pipeline_schedules(project_and_group)
    for schedule in schedules:
        gl.delete_pipeline_schedule(project_and_group, schedule["id"])


def run_gitlabform(config, target, include_archived_projects=True):
    # f-strings with """ used as configs have the disadvantage of having indentation in them - let's remove it here
    config = textwrap.dedent(config)

    # we don't want to repeat ourselves in the tests, so prefix the configs with this mandatory part here
    config = CONFIG + config

    gf = GitLabForm(
        include_archived_projects=include_archived_projects,
        config_string=config,
        target=target,
    )
    gf.run()
