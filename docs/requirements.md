# Requirements

!!! important
  
  Support for GitLab versions earlier than 16.x is DEPRECATED and will be removed in GitLabForm v7


* Built on Python 3.14, backwards-compatible to Python 3.12
    * you can use Docker image or [pyenv](https://github.com/pyenv/pyenv) if your OS does not have a required Python version
* Self-Hosted GitLab 14.4+ or SaaS GitLab @ gitlab.com
    * Premium (paid) license for some features

!!! note

  1. GitLabForm is built and tested against [`gitlab-ee/latest`](https://hub.docker.com/r/gitlab/gitlab-ee/tags), so some features may require a newer version.
  2. Some features may not be available in SaaS GitLab @ gitlab.com because of gitlab.com's limitations.