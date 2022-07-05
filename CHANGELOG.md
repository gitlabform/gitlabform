## Changelog

### 3.0.0

This is mostly a maintenance release that lays the ground for the future user-facing improvements. It is a major version bump because of the backward-incompatible changes, see below:

* Bump the minimal GitLab version to 14.4 (released in Oct 2021) (as it contains the [required API rename](https://gitlab.com/gitlab-org/gitlab/-/issues/334500)),
* Bump the minimal required Python version to 3.7 (as 3.6 is EOL since Dec 2021),
  * Update many dependencies that have required Python >= 3.7,
* Drop the Debian-based Docker image (it's nearly unused - you can maintain your own, if you needed it),
* Drop support for a lot of deprecated configuration syntax that the app has warned about: 
  * branch protection - no more `developers_can_push`, `developers_can_merge`, use `push_access_level`, `merge_access_level` etc. instead,
  * group members - no more `group_shared_with`, `enforce_group_members`, `group_access_level`, use `group_members`, `group_members.enforce`, `group_access` instead,
  * services/integrations - no more `recreate`,
* Follow the renames in GitLab and rename some configuration sections:
  * `services` -> `integrations`,
  * `secret_variables` -> `variables`,
  * `group_secret_variables` -> `group_variables`,
* (Applies only to the users of this app as library) Rename some API methods, remove deprecated ones,
  * `protect_branch()` is now the method using the new API, the method using the old one has been removed,
  * `branch_code_owner_approval_required()` -> `set_branch_code_owner_approval_required()`.
  * `delete_legacy_approvers()` has been removed,
  * all the methods with `service(s)`/`secret_variable(s)`/`group_secret_variable(s)` in their names have been renamed to contain `integration(s)`/`variable(s)`/`group_variables(s)`.
* Shorter and easier to read errors (full stacktrace shown only when `--debug` is enabled),

### 2.12.0

* Update base Docker images:
  * from Python 3.9 and Alpine 3.14 to Python 3.10 and Alpine 3.16,
  * from Python 3.9 and Debian 10 (Buster) to Python 3.10 and Debian 11 (Bullseye).
* Fix Group CI/CD Variables not honoring `protected` and `masked` values set to `false`. Fixes [#384](https://github.com/gitlabform/gitlabform/issues/384).

### 2.11.1post3

* Moved the project from `gdubicki/gitlabform` to `gitlabform/gitlabform`. Stopped publishing new images to the old `egnyte/gitlabform` Docker registry.

### 2.11.1

* Fix another case of GitLab's Schedules API change/bug. Fixes [#364](https://github.com/gitlabform/gitlabform/issues/364).

### 2.11.0

* **Allow breaking configuration inheritance**. Implements [#326](https://github.com/gitlabform/gitlabform/issues/326). PR [#339](https://github.com/gitlabform/gitlabform/pull/339).

Imagine you have a configuration like this:
```yaml
projects_and_groups:
  my-group/*:
    members:
      enforce: true
      groups:
        regular-developers:
          group_access: developer
 
  my-group/special-private-project:
    members:
      inherit: false # <--- the new keyword
      enforce: true
      groups:
        special-developers:
          group_access: developer
      users:
        john:
          access_level: maintainer
```
With the new `inherit: false` entry used here, the effective members for `my-group/special-private-project` project are ONLY the `special-developers` grup and `john` user.

* Always expect pagination for GETs. Fixes [#354](https://github.com/gitlabform/gitlabform/issues/354). PR [#358](https://github.com/gitlabform/gitlabform/pull/358).
* Workaround for the GitLab's Schedules API change/bug. Fixes [#361](https://github.com/gitlabform/gitlabform/issues/361).

<br/>

Big thanks to the [Elastic Path](https://www.elasticpath.com/) team for their contribution of the above feature, especially [@ep-linden](https://github.com/ep-linden) for the whole implementation and [@amimas](https://github.com/amimas) for the initial proposal and cooperation on design!

<br/>

(There were 4 pre-releases of this version, 2.11.0b1-b4. b1 contained "Allow breaking configuration inheritance", b2 also [#358](https://github.com/gitlabform/gitlabform/pull/358), b3 also a fix of a bug that caused breaking config inheritance to not work in some cases, b4 - [#361](https://github.com/gitlabform/gitlabform/issues/361)).

### 2.10.1

* Fix a problem causing some changes to not be applied. Fixes [#334](https://github.com/gitlabform/gitlabform/issues/334). PR [#350](https://github.com/gitlabform/gitlabform/pull/350).

### 2.10.0

* **Deleting deploy keys is now possible**. This partially implements [#193](https://github.com/gitlabform/gitlabform/issues/193). Also completely replace the implementation of deploy keys, secret variables and group secret variables with a new universal one. This possibly fixes [#19](https://github.com/gitlabform/gitlabform/issues/19).
* **Up to 40% faster thanks to making less requests to GitLab.** (For almost 1000 repositories the apply time has dropped from ~18 minutes to ~11 minutes.)
* With debug enabled a lot less duplication and a more readable output of dicts (shown as JSONs).
* **For Contributors** Introduce `SingleEntityProcessor` that generalizes editing things that are single per project, f.e. settings or push rules set. It does not edit entities if there are not changes to be applied. Using it implementing new features can be superfast! (See also `MultipleEntitiesProcessor` added in v2.2.0).
* **For Contributors** Faster tests and improved usage of fixtures.

(A pre-release of 2.9.2 RC1 contained some of the above changes. 2.10.0rc1 pre-release was the same as 2.10.0 final but with a slightly different changelog - the speed gains turned out to be higher than expected.)

### 2.9.1

* Fix version 2.9.0 not even starting. 🤦‍♂️ Add test to prevent this from happening again.

### 2.9.0

* **Access level names (not only their numbers) are now accepted in the configuration**.
* More strictness in parsing configuration YAML and better error messages thanks to a switch to different libraries. F.e. hash keys overwriting is not accepted anymore.
* Moved the project from `egnyte/gitlabform` to `gdubicki/gitlabform` and switch to GitHub Registry as the new main Docker registry.

### 2.8.1

* Don't show "Warning: Using group_shared_with: is deprecated" although the user is not really using this config syntax.

### 2.8.0

* **Complete support for managing groups and projects members**:
  * Add enforcing (direct) project members - groups and users, including being able to remove all direct members and keep only the members inherited from the group. Implements [#100](https://github.com/gitlabform/gitlabform/issues/100).
  * Unify the configuration syntax for group and project level membership.

✨ **New** ✨ config syntax example:
```yaml
projects_and_groups:
  foo/*:
    # below key now includes what used to be under 
    # `group_shared_with` and `enforce_group_members` keys
    group_members:
      # there are only up to 3 direct keys below
      groups:
        another-group:
          # below key's name been changed to the name used in projects `members`
          # for groups (and the same as in the API to share group with group)
          group_access: 30
      users:
        my-user:
          access_level: 50 # owner
      # this will enforce group-level users to be ONLY as defined above
      enforce: true

    # this will make the projects in `foo` group not contain any **direct** users or groups other
    # (so it will make it contain only the ones inherited from the group `foo`)
    members:
      enforce: true
```
The 🏚 old and deprecated 🏚 syntax for a similar* config would be:
```yaml
projects_and_groups:
  foo/*:
    group_shared_with:
      groups:
        another-group:
          group_access_level: 30
    group_members:
      my-user:
        access_level: 50 # owner
    enforce_group_members: true

    # !!! * - there was no enforce project members support before v2.8.0 !!!
```
The old syntax works but will generate warnings. Support for it will be removed in one the future major GitLabForm versions.

### 2.7.1

* Speed up running for `ALL_DEFINED`, when the defined groups and projects for just a small part of all the GitLab instance's groups and projects. Additionally **always** show the number of omitted groups and projects for any reasons (no config, archived, skipped). Fixes [#285](https://github.com/gitlabform/gitlabform/issues/285).

### 2.7.0

* **Allow processing only requested configuration sections** using a new cli argument `-os / --only-sections`.
* Minimize the number of unnecessary audit branch unprotect/protect events. Up to now every apply of the `files` section for protected branch resulted in unprotect and then (re)protect event for each protected branches and each file. Now this will only happen when the user running GitLabForm actually needs to do that, which should not happen often if you are using an admin account. Completely fixes [#178](https://github.com/gitlabform/gitlabform/issues/178).

### 2.6.0

* **Complete support for Protected branches - access levels / users / groups allowed to push/merge/unprotect** (**GitLab Premium (paid) only**). PR [#289](https://github.com/gitlabform/gitlabform/pull/289).
* **Add option to allow push force in protected branches**. Implements [#227](https://github.com/gitlabform/gitlabform/issues/227).
* Fix a bug causing the app to get HTTP 502 from GitLab when protecting branches in some cases.
* Fix getting members list to include usernames of all direct members not just the first page. PR [#284](https://github.com/gitlabform/gitlabform/pull/284).

Big thanks to the contributors of this release: [@trissanen](https://github.com/trissanen)

### 2.5.0

* **Make commit messages for file operations configurable.** Implements [#278](https://github.com/gitlabform/gitlabform/issues/278).

Thanks to [@aleung](https://github.com/aleung) for his contribution!

### 2.4.0

* **Add wildcard support for `skip_groups` and `skip_projects`.** Implements [#275](https://github.com/gitlabform/gitlabform/issues/275) and [#276](https://github.com/gitlabform/gitlabform/issues/276).

Thanks to [@chris-workingmouse](https://github.com/chris-workingmouse) for his contribution!

### 2.3.0

* **Add Protected branches - users allowed to push/merge** (**GitLab Premium (paid) only**), PR [#273](https://github.com/gitlabform/gitlabform/pull/273).
* For `ALL_DEFINED` also skip archived projects even if they are explicitly defined in the config, unless -a flag is added - for consistency.
* **For Contributors** Add docs for running the test themselves in a Docker container and for running GitLab in Docker using a license file, for testing paid-only features.

Thanks to [@florentio](https://github.com/florentio), [@barryib](https://github.com/barryib) and [@Pigueiras](https://github.com/Pigueiras) for their contribution!

### 2.2.0

* **Add LDAP Group Links support** (**GitLab Premium (paid) only**). Implements [#140](https://github.com/gitlabform/gitlabform/issues/140).

* **Add project and group badges support**. Implements [#59](https://github.com/gitlabform/gitlabform/issues/59).

* Allow 0 (no access) in Protected Tags. Fixes [#172](https://github.com/gitlabform/gitlabform/issues/172).

* Exit on configuration missing `projects_and_groups` key. This will provide a helpful error message for typos made in this key. Fixes [#242](https://github.com/gitlabform/gitlabform/issues/242).
* Make error messages more friendly when there is no network connection or when configuration is invalid (f.e. YAML parsing errors).
* Make the output of some processors a bit more consistent.

* Fix detecting an "empty effective config" and improve the UI related to processing groups and projects with such. Fixes [#251](https://github.com/gitlabform/gitlabform/issues/251).

* Big refactoring that should make adding new features easier and faster. The main change is introducing a new way to implement "processors" - thanks to a generalized `MultipleEntitiesProcessor` class adding a new feature like Project Badges should is now as easy as implementing a class like `BadgesProcessor` and writing an acceptance test like `TestBadges`. Note that this new design may change in the near future and we are open to discussions and PRs to make it even better! We also plan to create a similar generalized `SingleEntityProcessor` class soon.

* Change the User Agent that the app uses when making requests to GitLab to a custom `GitLabForm/<gitlabform_version> (python-requests/<requests_version>)`.

### 2.1.2

* Managing project members is not incredibly slow anymore. Fixes [#240](https://github.com/gitlabform/gitlabform/issues/240)

Thanks to [@andrewjw](https://github.com/andrewjw) (Ocado Technology) for his contribution!

### 2.1.1

* Fixed sharing group with a subgroup. Fixes [#236](https://github.com/gitlabform/gitlabform/issues/236)
* Improved re-protecting branches after updating files in them. Fail fast if the config is invalid.
* Better Docker images:
  * Updated Alpine from 3.12 to 3.14,
  * Started to build images in ARM64 architecture (apart from x86-64),
  * Started to add tags <major_version>, <major_version>.<minor_version>. Note that Alpine-based image is the main one which gets these tags. For Debian-based images add "-buster" suffix. Implements [#173](https://github.com/gitlabform/gitlabform/issues/173)

Thanks to [@andrewjw](https://github.com/andrewjw) (Ocado Technology) for his contribution!

### 2.1.0

* **Added a feature to share groups with other groups, with optional enforcing.** Implements [#150](https://github.com/gitlabform/gitlabform/issues/150)

Thanks to [@andrewjw](https://github.com/andrewjw) (Ocado Technology) for this contribution!

### 2.0.6

* Fixed incorrect subgroups list when requesting to process ALL_DEFINED. Completes the fix for [#221](https://github.com/gitlabform/gitlabform/issues/221)

### 2.0.5

* *Really* fixed issue with `unprotect_branch_new_api`. Fixes [#219](https://github.com/gitlabform/gitlabform/issues/219)
* Fixed call to a Merge Requests Approvers API endpoint removed in GitLab 13.11.0. Fixes [#220](https://github.com/gitlabform/gitlabform/issues/220)
* Fixed potential security issue by enabling autoescaping when loading Jinja templates. (Bandit security tool issue [B701](https://bandit.readthedocs.io/en/latest/plugins/b701_jinja2_autoescape_false.html))

Thanks to [@Pigueiras](https://github.com/Pigueiras) for his contribution!

### 2.0.4

* Fixed issue with Push Rules when the project name contains a dot. Fixes [#224](https://github.com/gitlabform/gitlabform/issues/224)
* Fixed calling to process a single subgroup (like: `gitlabform 'group/subgroup'`). Fixes [#221](https://github.com/gitlabform/gitlabform/issues/221)

### 2.0.3

* Fixed issue with dry-run for Project Push Rules when the current config is empty (`None`). Fixes [#223](https://github.com/gitlabform/gitlabform/issues/223)

### 2.0.2

* Fixed issue with `unprotect_branch_new_api`. Fixes [#219](https://github.com/gitlabform/gitlabform/issues/219)
  (update: later it turned out that it was not really fixed in 2.0.2 but in 2.0.5 instead)

### 2.0.1

* Fixed issues with Jinja loader.
* Fixed calls to GitLab API that do not contain 'x-total-pages' header (gradually rolled out since [GitLab MR #23931](https://gitlab.com/gitlab-org/gitlab-foss/-/merge_requests/23931)).
* Start showing deprecation warning when using the old branch protection API config syntax.

Thanks to [@mkjmdski](https://github.com/mkjmdski) for his contribution!

(2.0.0post1-3 release is technically the same as 2.0.1 but was incorrectly versioned.)

### 2.0.0

(For a detailed info about changes in each RC of v2 please see the previous version of this changelog.)

* **Make deep merging of configuration actually work (breaking change).** Fixes [#197](https://github.com/gitlabform/gitlabform/issues/197) (RC5)

* **Introduce config versioning (breaking change).** ...or rather a change to avoid breakage. New major releases of GitLabForm starting with v2 will look for `config_version` key in the config file. If it doesn't exist, or the version does not match expected then the app will exit to avoid applying unexpected configuration and allowing the user to update the configuration. (RC1)

* **New config syntax (breaking change).** All 3 levels under a common key `projects_and_groups`. It should contain a dict, where common config is under a special `"*"` key, group configs under keys like `group/*` and project configs under keys like `group/project`. This will allow introducing pattern matching in these keys and introducing support for multiple config files in the future releases. Partially implements [#138](https://github.com/gitlabform/gitlabform/pull/138). (RC1)

* **Exit with code != 0 when any group/project processing was failed (breaking change).** This will allow you to notice problems when running the app from CI. Note that you can restore the old behaviour by running the app with `(...) || true`. Also **standardized exit codes.** Exit with 1 in case of input error (f.e. config file does not exist), with 2 in case of processing error (f.e. GitLab returns HTTP 500).Fixes [#153](https://github.com/gitlabform/gitlabform/issues/153). (RC1)

* **Allow any case in groups and projects names (breaking change).** GitLab groups and projects names are case sensitive but you cannot create such entities that differ only in the case. There is also a distinction between a "name" and a "path" and they may differ in case... To make work with this easier GitLabForm now accepts any case for them in both config files as well as when provided as command line arguments. We also disallow such entities that differ only in case (f.e. `group/*` and `GROUP/*`) to avoid ambiguity. Fixes [#160](https://github.com/gitlabform/gitlabform/issues/160). (RC2)

* **Ignore archived projects by default (breaking change).** This makes processing faster and output shorter. You can restore the previous behavior by adding `--include-archived-projects`/`-a` command line switch. Note that you have to do it if you want to unarchive archived projects! Fixes [#157](https://github.com/gitlabform/gitlabform/issues/157) in (arguably) a more convenient way. (RC2)

* **Color output!** Implements [#141](https://github.com/gitlabform/gitlabform/issues/141). (RC1)

* **Add diffing feature for secret variables.** (with values shown as hashes to protect the secrets from leaking). (RC6)

* **Added checking for invalid syntax in "members" section.** Defining groups or users directly under this key instead of under sub-keys "users" and "groups" will now trigger an immediate error. (RC5)

* **Add support for Python 3.9** (RC8)

* **Added Windows support.** Fixes [#206](https://github.com/gitlabform/gitlabform/issues/206) (RC5)

* **Start processing at any group** using the new command line switch - `--start-from-group`/`-sfg`. Similar to `--start-from`/`-sf` switch that can be used for projects. (RC1)

* Start releasing pre-releases as Docker images. They have tags with specific versions, but not "latest" tag as it is reserved for new final releases. Implements [#201](https://github.com/gitlabform/gitlabform/issues/201) (RC5)

* Prevent multiple email notifications from being sent when adding members to project. Fixes [#101](https://github.com/gitlabform/gitlabform/issues/101) (RC6)

* Prevent project's Audit Events being filled in with "Added protected branch". Fixes [#178](https://github.com/gitlabform/gitlabform/issues/178) (RC6)

* Fixed using "expires_at" for users. Fixes [#207](https://github.com/gitlabform/gitlabform/issues/207) (RC6)

* Remove the need to add the `gitlab.api_version` configuration key. (RC1)

* **For Contributors** Make writing tests easier and the tests more robust. Deduplicate a lot of the boilerplate code, allow putting configs into the test methods and use pytest fixtures for easier setup and cleanup. This should fix issues with tests reported in [#190](https://github.com/gitlabform/gitlabform/issues/190). Also stop storing any dockerized GitLab data permanently to avoid problems like [#196](https://github.com/gitlabform/gitlabform/issues/196) and probably other related to failed dockerized GitLab upgrades. (RC3)

* **For Contributors** Rename "integration tests" to "acceptance tests". Because they ARE in fact acceptance tests. (RC3)

Thanks to [@amimas](https://github.com/amimas), [@weakcamel](https://github.com/weakcamel), [@kowpatryk](https://github.com/kowpatryk), [@ss7548](https://github.com/ss7548), [@houres](https://github.com/houres), [@Pigueiras](https://github.com/Pigueiras) and [@YuraBeznos](https://github.com/YuraBeznos) for their contributions!

### before 2.0.0

Please see [GitHub pre-2.0 releases' descriptions](https://github.com/gitlabform/gitlabform/releases?after=v2.0.0rc1).
