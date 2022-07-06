# Automation

## Running in an automated pipeline

You can use GitLabForm as a part of your [CCA (Continuous Configuration Automation)](https://en.wikipedia.org/wiki/Continuous_configuration_automation) pipeline.

You can run it with a schedule on `ALL_DEFINED` or `ALL` projects to unify your GitLab configuration, after it may have drifted
from the configuration. For example you may allow the users to reconfigure projects during their working hours
but automate cleaning up the drift each night.

An example `.gitlab-ci.yml` for running GitLabForm using GitLab CI is provided here:
```yaml
image: ghcr.io/gdubicki/gitlabform:latest

some_project:
  only:
    changes:
    - config.yml
  script: gitlabform my-group/subgroup/project

my_whole_other_group:
  only:
    changes:
    - other-config.yml
  script: gitlabform -c other-config.yml my_whole_other_group
```

Note that as a standard best practice you should not put your GitLab access token in your `config.yml` (unless it is
encrypted) for security reasons - please set it in the `GITLAB_TOKEN` environment variable instead.

For GitLab CI a secure place to set it would be a [Protected Variable in the project configuration](https://docs.gitlab.com/ee/ci/variables/#protected-cicd-variables).

## Running automatically for new projects

(* - Why do we provide a how-to only for the new projects and not groups?

Because we assume that there is no big need to automate configuring new groups as if you add a config for a new group
to GitLabForm, then it's hard to forget to actually run it...)

## Using system hooks

Probably all the methods to achieve this will use GitLab [system hooks feature](https://docs.gitlab.com/ee/system_hooks/system_hooks.html)
which makes GitLab perform HTTP POST request on - among other ones - these events:

* `project_create`
* `project_rename` - we want this because after the rename project may get a new config from GitLabForm,
* `project_transfer` - we want this because under a new group the project may get a new config from GitLabForm,

### Method 1: GitLabForm on the same server as GitLab + adnanh/webhook app

In this method we assume that:

* you have GitLabForm installed on the same server as your GitLab instance.
    * its binary is here: `/opt/gitlabform/venv/bin/gitlabform`.
    * its config is in `/opt/gitlabform/conf` - `config.yml` plus some files for the `files:` sections.


#### Step 1: Configure GitLab system hooks

Go to https://gitlab.your-company.com/admin/hooks and create a hook with the URL http://127.0.0.1:9000/hooks/run-gitlabform .
Uncheck all the extra triggers as the events that are interesting for us are among the standard ones.
Leave "Enable SSL verification" unchecked as we are making calls over loopback, there is no need to encrypt the traffic
here.

#### Step 2: Configure the webhook app to run GitLabForm

Get and install the [adnanh/webhook](https://github.com/adnanh/webhook) app.

Create this pretty self-explaining config:

```yaml
---
- id: run-gitlabform
  execute-command: "/opt/gitlabform/venv/bin/gitlabform"
  command-working-directory: "/opt/gitlabform/conf"
  pass-arguments-to-command:
  - source: payload
    name: path_with_namespace
  trigger-rule:
    match:
      type: regex
      regex: "(project_create|project_rename|project_transfer)"
      parameter:
        source: payload
        name: event_name
```

...and save it as `hooks.yaml`.

Run webhook app with:

```shell
./webhook -hooks path/to/your/hooks.yaml -ip 127.0.0.1 -verbose
```

...and keep it running.

(In the long term you should make this permanent with a systemd service/other way appropriate to your distro.)

#### Step 3: Test

Create a project with a config defined in your GitLabForm config and watch the output of webhook app.
It should look like this:

```
[webhook] 2021/01/25 19:24:56 incoming HTTP request from 127.0.0.1:56822
[webhook] 2021/01/25 19:24:56 run-gitlabform got matched
[webhook] 2021/01/25 19:24:56 200 | 180.402µs | 127.0.0.1:5000 | POST /hooks/run-gitlabform
[webhook] 2021/01/25 19:24:58 command output: *** # of groups to process: 0
*** # of projects to process: 1
* [1/1] Processing: your-group/your-project
(...)
GitLabForm version: 1.20.0 (the latest)
[webhook] 2021/01/25 19:24:58 finished handling run-gitlabform
```

- congrats! This means that it works! 🎉
