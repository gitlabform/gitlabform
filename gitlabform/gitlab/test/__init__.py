import os

from gitlabform.gitlab import GitLab
from gitlabform.gitlab.core import NotFoundException, UnexpectedResponseException

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

GROUP_NAME = "gitlabform_tests_group"

DEVELOPER_ACCESS = 30
OWNER_ACCESS = 50

gl = GitLab(config_string=CONFIG)


def get_gitlab():
    return gl
