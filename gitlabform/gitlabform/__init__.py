from gitlabform import Singleton
from gitlabform.gitlabform.core import GitLabFormCore


class GitLabForm(GitLabFormCore, metaclass=Singleton):
    pass
