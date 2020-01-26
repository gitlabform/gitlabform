[![PyPI version](https://badge.fury.io/py/gitlabform.svg)](https://badge.fury.io/py/gitlabform)
[![Build Status](https://travis-ci.com/egnyte/gitlabform.svg?branch=master)](https://travis-ci.com/egnyte/gitlabform)

# GitLabForm

GitLabForm is a specialized "configuration as a code" tool for GitLab projects, groups and more
using hierarchical configuration written in YAML.

## Table of Contents

* What you get? - [Features](#features) (& [Comparison to similar apps](#comparison-to-similar-apps))
* Basic usage - [Requirements](#requirements), [Installation](#installation), [Quick start](#quick-start)
* Advanced usage - [Full configuration syntax](#full-configuration-syntax), [More cli usage examples](#more-cli-usage-examples), [Running in an automated pipeline](#running-in-an-automated-pipeline)
* Join us! - [Contributing](#contributing), [History](#history), [License](#license)

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
* Merge Requests approvals settings and approvers (**GitLab EE only**),

...for:

* all projects in your GitLab instance/that you have access to,
* a group/subgroup of projects,
* a single project,

...and a combination of them.

GitLabForm uses [hierarchical configuration with inheritance, merging/overwriting and addivity](FEATURES_DESIGN.md#hierarchical-merged-and-overridable-configuration). GitLabForm is also
using [passing the parameters as-is to GitLab APIs with PUT/POST requests](FEATURES_DESIGN.md#raw-parameters-passing).

### Comparison to similar apps

GitLabForm has roughly the same purpose as [GitLab provider](https://www.terraform.io/docs/providers/gitlab/index.html)
for [Terraform](https://www.terraform.io/) (which is a tool that we love and which has inspired us to write this app),
but it has a different set of features and uses a different configuration format.

Please read more about [GitLab provider for Terraform vs GitLabForm](GT_VS_GLF.md). This article includes a link to the feature matrix / comparison sheet between these two tools.

## Requirements

* Python 3.5+ or Docker
* GitLab 11+, GitLab EE for Merge Requests management

## Installation

A. Pip: `pip3 install gitlabform`

B. Docker: run GitLabForm in a Docker container with this oneliner:
`docker run -it -v $(pwd):/config egnyte/gitlabform:latest gitlabform`.
Instead of "latest" you can also use a specific version and choose from Alpine and Debian-based images.
See the [GitLabForm's DockerHub page](https://hub.docker.com/r/egnyte/gitlabform/tags) for a list of available tags.

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

## Full configuration syntax

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

You can use GitLabForm as a part of your [CCA (Continuous Configuration Automation)](https://en.wikipedia.org/wiki/Continuous_configuration_automation) pipeline.

For example, you can run it:
* with a schedule to unify your GitLab configuration each night, after it may have drifted
from the configuration in the code during the working day.
* from a webhook after a new project is created in GitLab to have have the initial config
for new projects done automatically as soon as the projects are created.

Example for running GitLabForm using GitLab CI is provided in the [.gitlab-ci.example.yml](.gitlab-ci.example.yml) file.

Note that as a standard best practice you should not put your GitLab access token in your `config.yml` (unless it is 
encrypted) for security reasons - please set it in the `GITLAB_TOKEN` environment variable instead.

For GitLab CI a secure place to set it would be a [Secret/Protected Variable in the project configuration](https://docs.gitlab.com/ee/ci/variables/#via-the-ui).

## Contributing

Contributions are very welcome! We do not have strict requirements for Pull Requests yet, so if you want to add your features quickly then this is the best time to do it. ;) But seriously: the usual rules apply - working, readable, commented code with squashed commits with helpful messages is preferred.

Please start with reading the [features design article](FEATURES_DESIGN.md) to get to know the app's basic design concepts.

Development environment setup how-to:

1. Create virtualenv with Python 3.5+, for example in `venv` dir which is in `.gitignore` and activate it:
```
virtualenv -p python3 venv
. venv/bin/activate
```

2. Install build requirements - `pandoc` binary package + `pypandoc` python package:
```
# for macOS:
brew install pandoc  
pip3 install pypandoc
```

3. Install gitlabform in develop mode:
```
python setup.py develop
```

### Running unit tests locally

GitLabForm uses py.test for tests. To run unit tests locally:

1. Activate the virtualenv created above

2. `pip install pytest`

3. Run `then py.test --ignore gitlabform/gitlabform/test` to run all tests except the integration tests (see below).

### Running integrations tests locally or on own GitLab instance

GitLabForm also comes with a set of tests that make real requests to a running GitLab instance. You can run them
against a disposable GitLab instance running as a Docker container OR use your own GitLab instance.

To run them against a local GitLab instance:

1. Run below commands to start GitLab in a container. Note that it may take a few minutes!

```
./run_gitlab_in_docker.sh
export GITLAB_URL=$(cat gitlab_url.txt)
export GITLAB_TOKEN=$(cat gitlab_token.txt)
```

2. Run `py.test gitlabform/gitlabform/test` to start the tests

**Note**: although GitLabForm integration tests operate own their own groups, projects and users, it should be safe
to run them against your own GitLab instance, but we do to take any responsibility for it. Please review the code
to ensure what it does and run on your own risk.

To run them against your own GitLab instance:

1. Get an admin user API token and put it into `GITLAB_TOKEN` env variable. Do the same with your GitLab instance URL
and `GITLAB_URL`:
```
export GITLAB_URL="https://mygitlab.company.com"
export GITLAB_TOKEN="<my admin user API token>"
```

2. Run `py.test gitlabform/gitlabform/test` to start the tests

## History

This tool was originally created as a workaround for missing GitLab features such as [assigning deploy keys per project groups](https://gitlab.com/gitlab-org/gitlab-ce/issues/3890)
but as of now we prefer to use it ever if there are appropriate web UI features, such as [secret variables per project groups](https://gitlab.com/gitlab-org/gitlab-ce/issues/12729)
(released in GitLab 9.4) to keep the configuration as code.

Later on we added features that allowed us to use GitLabForm to improve a group containing around 100 similar projects
to move to a unified development flow (by managing branches protection and the Pull Requests configuration),
basic tests and deployment process (by managing secret variables, deployment keys and files, such as `.gitlab-ci.yml`),
integrations (such as JIRA or Slack) and more.

## License

MIT
