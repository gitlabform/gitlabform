# Implementation design

If you haven't done this before, please read the [configuration introduction](../reference/index.md) article first.

It explains the "**why**"s of the two key design concepts of this app:

* hierarchical configuration with inheritance, merging/overwriting and additivity,
* raw parameters passing

Please also read the general [coding guidelines](coding_guidelines.md) for the basics of how to create PRs,
the expected style of your code etc. - the "**general how**"s.

This article purpose is to explain "**specific how**"s - explain what is where in the code and how to add features
by example.

## Calling GitLab REST APIs

We prefer to call GitLab's REST APIs using [`python-gitlab`](https://python-gitlab.readthedocs.io/en/stable/) rather than creating our own REST implementations.

A python_gitlab instance `./gitlabform/gitlab/python_gitlab.py` is provided on `AbstractProcessor`, extending the base functionality to add convenience methods and caching to common GET requests. It will not always be appropriate to call a `_cached` method, as you will require the updated instance of a given Object after performing CRUD operations upon it. 

## Project Structure

### Packages overview

* `gitlabform.*`, `gitlabform.lists.*` and `gitlabform.processors.*` - these contain the main app logic.
  They provide the CLI, parsing of the parameters (`gitlabform.*`), getting the input lists of groups and projects
  to process and omitting unneeded ones to get the effective lists (`gitlabform.lists.*`) and finally processors
  are used to apply the groups and projects configurations in GitLab,

* `gitlabform.gitlab.*` - contains the GitLab API client code, grouped mostly by the GitLab API 
  [as documented at docs.gitlab.com](https://docs.gitlab.com/ee/api/api_resources.html).

* `gitlabform.configuration.*` - contains the logic for reading the config from YAML file or a string
  (the latter is only for testing) and getting an effective config per GitLab project by merging
  the config on these levels: common, group and project settings.

Please see the below doc sections for more info about these packages.

### gitlabform.*, gitlabform.lists.* and gitlabform.processors.*

The entry point for running the app is in `run.py` and the main logic is in the `GitLabForm` class.

This code boils down to the `run()` method, which for each project that according to the app parameters
and config should be taken into account, applies the effective config.

The code in `gitlabform.lists.*` is used to generate the input lists of groups and projects, omit the ones that can and should be omitted for saving the processing time (f.e. archived projects, groups and projects with empty effective config) and this way generate the effective lists of groups and projects.

The effective config for these contain what is called the "config sections", which are the YAML keys that can exist under projects
in the config YAML, for example: `deploy_keys`, `variables`, `group_variables` and so on.

Those config sections are processed by the code in the classes inheriting from the `AbstractProcessor` class. This class
should be reused when implementing new functionalities (such as supporting new configuration keys) as it holds the common 
logic for skipping the configuration parts and running in dry-run mode. The processors have been grouped into two 
packages - `group` where the processors applied to the group settings are implemented and `project` - where processors
executed on the project level are located.

Processors call the GitLab API through `python-gitlab` (available as `self.gl`). For features that manage
0-N entities of some kind under a group or a project, see `DeployKeysProcessor` or `GroupLDAPLinksProcessor`
as examples of the common pattern: list the existing entities, match them against the config by their
identifying fields, and apply the changes (add, update or delete, and optionally `enforce`). The order of
these operations differs per processor, where API constraints demand it.

#### Usage

If you want to **add/change/fix things under an existing config section** then most likely you will need to update 
the code in the processor classes (for example, in `BranchesProcessor`).

If you want to **add support for a new config section** (= completely new feature), then you need to:

1. Create a new class `group_<new_config_section_name>_processor` (if it applies to the group settings) or 
`<new_config_section_name>_processor` (if it applies to project settings) and implement two methods:
    - `_process_configuration` - which does the actual processing by calling the API and applying the changes in GitLab;
    - `_log_changes` - which is optional but recommended to implement; by calling this method the effective changes 
    to be applied should be logged (when running in dry-run mode). 
2. Add the new processor to `GroupProcessors` in `group > __init__.py` (if group settings processor was created) or 
to `ProjectProcessors` in `project > __init__.py`. 

### gitlabform.gitlab.*

This package contains two things:

* `python_gitlab.py` - the `PythonGitlab` class that extends `python-gitlab`'s `Gitlab` class with
  convenience methods and caching used throughout the app. This is the place to add shared helpers
  for calling the GitLab API.
* `core.py` - the legacy `GitLabCore` class, which reads the app configuration, sets up the HTTP
  session and checks the GitLab version and the connected user. A few configuration transformers
  still use its helpers; the long-term plan is to move the rest of this to `python-gitlab` as well
  (see [issue #73](https://github.com/gitlabform/gitlabform/issues/73)).

Do not add new REST client code to `core.py`: new code should use `python-gitlab`, through `PythonGitlab`.

Sometimes some logic is needed around the API calls, for example because some GitLab APIs return
invalid HTTP error codes, like 404 instead of 400 - see `GroupLDAPLinksProcessor._create_link` as an example.

### gitlabform.configuration.*

The core code in this package contains some share code, which apart from the rather obvious things like parsing the input YAML, getting the value from a specific subkey and merging configs, contains also:

* code for breaking configuration inheritance using `inherit: false`,
* dealing with groups and project names in GitLab being de facto case-insensitive (you can change case of such entities name, but you cannot have 2 which names differ only in case) (see "almost duplicates" in the code),

The class inheritance order in this package (core -> common -> groups -> projects) is intentional, as common config affects groups configs and this in turn affects projects configs.

The effective configuration for a project may contain elements that are inherited from the common level and from the group level.

A separate module in this package, `transform.py`, contains code that does YAML-level transformation form allow a more user-friendly config syntax that is later replaced with a syntax required by GitLab API. An example of this can be accepting `user: <username>` in the input config syntax but internally transforming it into `user_id: <id_number>`.
