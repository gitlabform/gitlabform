# Implementation design

If you haven't done this before, please read the [main concepts](../main_concepts.md) article first.

It explains the "why"s of the two key design concepts of this app:
* hierarchical configuration with inheritance, merging/overwriting and additivity,
* raw parameters passing

Please also read the general [coding guidelines](coding_guidelines.md) for the basics of how to create PRs,
the expected style of your code etc. - the "general how"s.

This article purpose is to explain "specific how"s - explain what is where in the code and how to add features
by example.

## Project Structure

### Packages

* `gitlabform.*` and `gitlabform.processors.*` - contains the main app logic. It provides the CLI, parsing of the parameters,
  uses below two packages to apply the config defined in `config.yml` to the requested set of projects.

* `gitlabform.gitlab.*` - contains the GitLab API client code, grouped mostly by the GitLab API 
  [as documented at docs.gitlab.com](https://docs.gitlab.com/ee/api/api_resources.html).

* `gitlabform.configuration.*` - contains the logic for reading the config from YAML file or a string
  (the latter is only for testing) and getting an effective config per GitLab project by merging
  the config on these levels: common, group and project settings.

## Common pattern - multiple inheritance

In many of the above packages we are using _multiple inheritance_.
 
The basic features are implemented in the "core" class defined in `core.py`. Extensions to it are defined in all other
files as "feature" classes that inherit the "core". Finally, there is an "everything" class that groups them all - it is
defined in the `__init__.py` file.

### gitlabform.* and gitlabform.processors.*

The entry point for running the app is in `run.py` and the main logic is in the `GitLabForm` class.

This code boils down to the `run()` method, which for each project that according to the app parameters
and config should be taken into account, applies the effective config.

The effective config contains what is called the "config sections", which are the YAML keys that can exist under projects
in the config YAML, for example: `deploy_keys`, `variables`, `group_variables` and so on.

Those config sections are processed by the code in the classes inheriting from the `AbstractProcessor` class. This class
should be reused when implementing new functionalities (such as supporting new configuration keys) as it holds the common 
logic for skipping the configuration parts and running in dry-run mode. The processors have been grouped into two 
packages - `group` where the processors applied to the group settings are implemented and `project` - where processors
executed on the project level are located.

Since v2.2.0 there is a new way of implementing processors - by inheriting form `MultipleEntitiesProcessor` class.
It should be applied for new features which manage 0-N entities of some kind under a group or a project.
See `BadgesProcessor` as an example how to use it.

Since v2.10.0 we have a similar solution for features where you manage a single entity - `SingleEntityProcessor` class.
See `ProjectPushRulesProcessor` as an example how to use it. 

#### Usage

If you want to **add/change/fix things under an existing config section** then most likely you will need to update 
the code in the processor classes (for example, in `BranchesProcessor`).

If you want to **add support for a new config section** (= completely new feature), then you need to:

0. (TODO: expand this sections) Consider writing a new processor using `MultipleEntitiesProcessor` class as a base.
1. Create a new class `group_<new_config_section_name>_processor` (if it applies to the group settings) or 
`<new_config_section_name>_processor` (if it applies to project settings) and implement two methods:
    - `_process_configuration` - which does the actual processing by calling the API and applying the changes in GitLab;
    - `_log_changes` - which is optional but recommended to implement; by calling this method the effective changes 
    to be applied should be logged (when running in dry-run mode). 
2. Add the new processor to `GroupProcessors` in `group > __init__.py` (if group settings processor was created) or 
to `ProjectProcessors` in `project > __init__.py`. 

### gitlabform.gitlab.*

With the basics for making requests to the GitLab API covered in the `GitLabCore` class in `core.py`, all other code
is simple (most of the time).

Almost all methods in other classes end up calling `self._make_requests_to_api`, which takes care of making the HTTP
GitLab API requests with proper authentication, pagination, retries, timeouts and more.

Sometimes there is some logic in these methods if:

* we only need a specific part of the response from GitLab API - see `GitLabProjects.get_all_projects()` as an example,
* some GitLab APIs need some workarounds for their bugs or documentation inconsistencies, like:
    * some APIs declare in the docs that they accept both "group/project" string OR a project id while in fact only the latter works - see `GitLabProjects.post_approvals()` as an example,
    * some APIs return invalid HTTP error codes, like 404 instead of 400 - see `GitLabGroupLDAPLinks.add_ldap_group_link` as an example.

**Note**: Some of the code here is **NOT used by the GitLabForm app**, but utilized by internal Egnyte
applications that have not yet switched to the more standard `python-gitlab`.

#### Usage

If you want to **add/change/fix code that operates on an existing GitLab API** you should look around 
the "feature" classes in this package (for example `GitLabMergeRequests` in `merge_requests.py`).

If you want to **add code that operates on the new GitLab API** you should:
 
1. create a new `new_gitlab_api_name.py` file in `gitlabform.gitlab` and define a "feature" class there
   that inherits `GitLabCore` (for example: `GitLabApiName`).
2. add the new feature class to the list of classes inherited by the "everything" `GitLab` class
   defined in `__init__.py`. 

### gitlabform.configuration.*

**TODO**: describe this part. Especially what an "effective project config" is, because that may not be clear.
