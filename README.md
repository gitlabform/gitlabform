[![PyPI version](https://badge.fury.io/py/gitlabform.svg)](https://badge.fury.io/py/gitlabform)
[![Build Status](https://travis-ci.org/egnyte/gitlabform.svg?branch=master)](https://travis-ci.org/egnyte/gitlabform)

# GitLabForm

GitLabForm is a specialized "configuration as a code" tool for GitLab projects, groups and more
using hierarchical configuration written in YAML.

## Features

GitLabForm enables you to manage:

* Group settings,
* Project settings,
* Archive/unarchive project,
* Project members (users and groups),
* Deployment keys,
* Secret variables (on project and group/subgroup level),
* Branches (protect/unprotect),
* Tags (protect/unprotect),
* Services,
* (Project) Hooks,
* (Project) Push Rules,
* (Add/edit or delete) Files, with templating based on Jinja2 (now supports custom variables!),
* Merge Requests approvals settings and approvers (EE 10.6+ only),

...for:

* all projects in your GitLab instance/that you have access to,
* a group/subgroup of projects,
* a single project,

...and a combination of them.

GitLabForm uses hierarchical configuration with inheritance, merging/overwriting and addivity. GitLabForm is also
using passing the parameters as-is to GitLab APIs with PUT/POST requests.
[Read more about these features here](FEATURES_DESIGN.md) .

### Similar apps

GitLabForm has roughly the same purpose as [GitLab provider](https://www.terraform.io/docs/providers/gitlab/index.html)
for [Terraform](https://www.terraform.io/) (which is a tool that we love and that clearly inspired this app),
but but it has a different set of features and uses a different configuration format.

[Please read more about "GitLab provider for Terraform" vs "GitLabForm", including a feature matrix, here](GT_VS_GLF.md).

## Requirements

* Python 3.5+
* GitLab 11+ for gitlabform >=1.0.0, GitLab 9.1-10.8 for gitlabform <1.0.0, (GitLab EE 10.6+ for merge_requests section)

## Installation

A. Pip: `pip3 install gitlabform`

B. Docker: you run GitLabForm in a Docker container with this oneliner:
`docker run -it -v $(pwd):/config egnyte/gitlabform:latest gitlabform`.
Instead of "latest" you can also use a specific version and choose from Alpine and Debian-based images.
See the [GitLabForm DockerHub](https://hub.docker.com/r/egnyte/gitlabform/tags) page for a list of available tags.

## Quick start

Let's assume that you want to add a deployment key to all projects in a group "My Group" (with path "my-group").
If so then:

1. Create example `config.yml`:

```yaml
gitlab:
  # You can also set in your environment GITLAB_URL
  url: https://gitlab.yourcompany.com
  # You can also set in your environment GITLAB_TOKEN
  token: "<private token of an admin user>"
  api_version: 4
  ssl_verify: true

group_settings:
  my-group:
    deploy_keys:
      a_friendly_deploy_key_name:  # this name is only used in GitLabForm config
        key: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC3WiHAsm2UTz2dU1vKFYUGfHI1p5fIv84BbtV/9jAKvZhVHDqMa07PgVtkttjvDC8bA1kezhOBKcO0KNzVoDp0ENq7WLxFyLFMQ9USf8LmOY70uV/l8Gpcn1ZT7zRBdEzUUgF/PjZukqVtuHqf9TCO8Ekvjag9XRfVNadKs25rbL60oqpIpEUqAbmQ4j6GFcfBBBPuVlKfidI6O039dAnDUsmeafwCOhEvQmF+N5Diauw3Mk+9TMKNlOWM+pO2DKxX9LLLWGVA9Dqr6dWY0eHjWKUmk2B1h1HYW+aUyoWX2TGsVX9DlNY7CKiQGsL5MRH9IXKMQ8cfMweKoEcwSSXJ
        title: ssh_key_name_that_is_shown_in_gitlab
        can_push: false
```

2. Run `gitlabform my-group`

3. Watch GitLabForm add this deploy key to all projects in "My Group" group in your GitLab!

## Configuration syntax

See [config.yml](https://github.com/egnyte/gitlabform/blob/master/config.yml) in this repo as a well documented example
of all the features, including configuring all projects in all groups, projects in "my-group" group and specifically
project "my-group/my-project1".

## More cli usage examples

To apply settings for a single project, run:

```gitlabform my-group/my-project1```

To apply settings for a group of projects, run:

```gitlabform my-group```

To apply settings for all groups of projects and projects explicitly defined in the config, run:

```gitlabform ALL_DEFINED```

To apply settings for all projects, run:

```gitlabform ALL```


Run:

```gitlabform -h```

...to see the current set of supported command line parameters.

## Running in an automated pipeline

You can use GitLabForm as a part of your [CCA](https://en.wikipedia.org/wiki/Continuous_configuration_automation) pipeline
to.

For example, you can run it with a schedule to unify your GitLab configuration each night, after it may have drifted
from the configuration in the code during the working day.

Or you can run the pipeline from a webhook after a new project is created in GitLab to have have the initial config
for new projects done automatically as soon as the projects are created.


Example for running GitLabForm using GitLab CI is provided in the `.gitlab-ci.example.yml` file.

Note that as a standard best practice you should not put your GitLab access token in your `config.yml` (unless it is 
encrypted) for security reasons - please set it in the `GITLAB_TOKEN` environment variable instead.

For GitLab CI a secure place to set it would be a [Secret/Protected Variable in the project configuration](https://docs.gitlab.com/ee/ci/variables/#via-the-ui)).

## History

This tool was originally created as a workaround for missing GitLab features such as [assigning deploy keys per project groups](https://gitlab.com/gitlab-org/gitlab-ce/issues/3890)
but as of now we prefer to use it ever if there are appropriate web UI features, such as [secret variables per project groups](https://gitlab.com/gitlab-org/gitlab-ce/issues/12729)
(released in GitLab 9.4) to keep the configuration as code.

Later on we added features that allowed us to use GitLabForm to improve a group containing around 100 similar projects
to move to a unified development flow (by managing branches protection and the Pull Requests configuration),
basic tests and deployment process (by managing secret variables, deployment keys and files, such as `.gitlab-ci.yml`),
integrations (such as JIRA or Slack) and more.

## Contributing

Development environment setup how-to:

1. Install build requirements - `pandoc` binary package + `pypandoc` python package.

2. Create virtualenv with Python 3.5+, for example in `venv` dir which is in `.gitignore`.

3. Activate the virtualenv and install gitlabform in it in develop mode (`python setup.py develop`).

## License

MIT
