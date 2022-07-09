!!! warning

    This site is not finished yet. See [PR #370](https://github.com/gitlabform/gitlabform/pull/370) for more information about its status.

    Until it is done, please see [the current app README](https://github.com/gitlabform/gitlabform/blob/main/README.md) and linked there articles for the up to date app docs.


![GitLabForm logo](images/gitlabform-logo.png){ align=left } 
is a specialized "configuration as a code" tool for GitLab projects, groups and more
using hierarchical configuration written in YAML.


## Why?

* **Short and powerful syntax.** A lot of features with a little amount of YAML thanks to the [hierarchical configuration with inheritance, merging/overwriting and additivity](configuration_reference/#effective-configuration) .
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

* **Dynamic features.** GitLab introduces new features monthly. You can often use them in GitLabForm without upgrading the app because we [pass some parameters as-is to GitLab APIs with PUT/POST requests](configuration_reference/#raw-parameters-passing).
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

## Used by

<a href="https://www.egnyte.com" target="_blank"><img src="https://www.egnyte.com/themes/custom/egnyte/logo.svg" width="130px" style="margin: 10px" alt="Egnyte logo"></a>
<a href="https://www.elasticpath.com" target="_blank"><img src="https://www.elasticpath.com/themes/custom/bootstrap_sass/logo.svg" width="130px" style="margin: 10px" alt="Elastic Path" /></a> ...and many more!
