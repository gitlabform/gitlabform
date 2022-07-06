!!! warning

    This site is not finished yet. See [PR #370](https://github.com/gdubicki/gitlabform/pull/370) for more information about its status.

    Until it is done, please see [the current app README](https://github.com/gdubicki/gitlabform/blob/main/README.md) and linked there articles for the up to date app docs.


![GitLabForm logo](images/gitlabform-logo.png){ align=left } 
is a specialized "configuration as a code" tool for GitLab projects, groups and more
using hierarchical configuration written in YAML.


## Why?

* **Short and powerful syntax.** A lot of features with a little amount of YAML thanks to the [hierarchical configuration with inheritance, merging/overwriting and additivity](main_concepts.md#hierarchical-merged-and-overridable-configuration) .
```yaml
  # configuration shared by all projects in this group...
  a_group/*:
    merge_requests:
      approvals:
        approvals_before_merge: 2
  # ...except this project that has a different config:
  a_group/a_special_project:
    merge_requests:
      approvals:
        approvals_before_merge: 1
```

* **Dynamic features.** GitLab introduces new features monthly. You can often use them in GitLabForm without upgrading the app because we [pass some parameters as-is to GitLab APIs with PUT/POST requests](main_concepts.md#raw-parameters-passing).
```yaml
  a_group/a_project:
    project_settings:
      # ALL the keys described at
      # https://docs.gitlab.com/ee/api/projects.html#edit-project
      # can be provided here
```

* **Stability.** We treat our users the way we would like to be treated by other software projects maintainers:
    * We follow [semver](https://semver.org/) and don't allow _existing features behavior changes_ in minor or patch versions.
    * Before changing the syntax we start printing _deprecation warnings_ in the versions before.
    * We use _versioning of the configuration syntax_ for major changes and provide step-by-step upgrade guidelines.

## Features

GitLabForm enables you to manage:

* Group:
    * Badges,
    * Members (users) {add/remove user, change access level, optional enforce},
    * Members (groups) {share/unshare with group, change access level, optional enforce},
    * [Members using LDAP Group Links](reference/group_ldap_links.md) (**GitLab Premium (paid) only**),
    * [CI/CD variables](reference/ci_cd_variables.md),
    * Settings,

* Project:
    * [Archive/unarchive](reference/archive_unarchive.md),
    * Badges,
    * [CI/CD variables](reference/ci_cd_variables.md),
    * [Protected branches](reference/protected_branches.md):
        * access levels (roles) allowed to push/merge/unprotect, allow force push flag,
        * users/groups allowed to push/merge/unprotect, code owner approval required flag (**GitLab Premium (paid) only**),
    * [Deploy keys](reference/deploy_keys.md),
    * Files {add, edit or delete}, with templating based on Jinja2 (now supports custom variables!),
    * Hooks,
    * Members (users) {add/remove user, change access level, optional enforce},
    * Members (groups) {share/unshare with group, change access level, optional enforce},
    * [Merge Requests approvals settings and approvers](reference/merge_requests.md) (**GitLab Premium (paid) only**),
    * Pipeline schedules,
    * [Push Rules](reference/push_rules.md) (**GitLab Premium (paid) only**),
    * Integrations,
    * [Settings](reference/project_settings.md),
    * Tags {protect/unprotect},

...for:

* all projects in your GitLab instance/that you have access to,
* a group/subgroup of projects,
* a single project,

...and a combination of them.

## Used by

<a href="https://www.egnyte.com" target="_blank"><img src="https://www.egnyte.com/themes/custom/egnyte/logo.svg" width="130px" style="margin: 10px" alt="Egnyte logo"></a>
<a href="https://www.elasticpath.com" target="_blank"><img src="https://www.elasticpath.com/themes/custom/bootstrap_sass/logo.svg" width="130px" style="margin: 10px" alt="Elastic Path" /></a> ...and many more!
