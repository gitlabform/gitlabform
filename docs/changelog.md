# Changelog

## 5.0.0-rc.2
Release Candidate including all the below.

## 5.0.0

### Breaking Changes

#### Branch Protection Updates [#1070](https://github.com/gitlabform/gitlabform/pull/1070) ([TimKnight-DWP](https://github.com/TimKnight-DWP) & [br0ziliy](https://github.com/br0ziliy))
When preventing GitlabForm from un-protecting and then re-protecting the Branch in order to apply configuration changes to the protection rules [#1070](https://github.com/gitlabform/gitlabform/pull/1070), we discovered some functionality that was previously hidden from the user.

Previously if you stopped defining `code_owner_approval_required` or `allow_force_push` in the YAML config, the settings would revert to the default Gitlab settings applied when first protecting the branch, see: [Branch Protection API](https://docs.gitlab.com/api/protected_branches/#protect-repository-branches)

With the changes to perform dynamic updates as required, we follow the GitlabForm convention of **leaving the Gitlab settings as is if the data is no longer defined in configuration**.

Therefore, if you wish to ensure the Protected Branch settings are applied as you intend when running GitlabForm you should define some defaults explicitly:

```yaml
projects_and_groups:
 my-group/*:
   branches:
     main:
       protected: true
       allow_force_push: false
       code_owner_approval_required: true
```

Full details: [docs/reference/protected_branches.md](reference/protected_branches.md)

- Extension of: https://github.com/gitlabform/gitlabform/pull/996

Resolves:
- https://github.com/gitlabform/gitlabform/issues/445
- https://github.com/gitlabform/gitlabform/issues/1061
- https://github.com/gitlabform/gitlabform/issues/1034

#### Renamed Group Level SAML Link config key [1175](https://github.com/gitlabform/gitlabform/pull/1175). ([amimas](https://github.com/amimas))

The group level saml link configuration syntax previously used `saml_group_links` as the config key name. 
This has been renamed to `group_saml_links` to be consistent with other group level configuration key of gitlabform. 
Docs changes have been included as well.

Resolves:
- [#1078](https://github.com/gitlabform/gitlabform/issues/1078)

#### Optimized Docker image [960](https://github.com/gitlabform/gitlabform/pull/960). ([gdubicki](https://github.com/gdubicki) & [amimas](https://github.com/amimas))

Introduces multi-layer builds and reduced dependency overheads.
This brings down the image size from 88.5MB (v4.8.0) to 68.5MB.

#### Upgrade Python-Gitlab to 8.0.0 [1178](https://github.com/gitlabform/gitlabform/pull/1178)

[Release Notes](https://github.com/python-gitlab/python-gitlab/releases/tag/v8.0.0)

#### Support only Python 3.14 onwards [1177](https://github.com/gitlabform/gitlabform/pull/1177). ([TimKnight01](https://github.com/TimKnight01))

Pyproject.toml supports >=3.14, the latest builds were tested on 3.12, but we wanted to make the break as part of this changeset.

### Bug Fixes

- Fix for Branch Protection changes, GitlabForm attempted to updated users when config has not changed from Gitlab, resulting in API errors and a failed run of GitlabForm. [#1107](https://github.com/gitlabform/gitlabform/pull/1107) ([TimKnight-DWP](https://github.com/TimKnight-DWP))

#### Variables with same name but different scope should be deletable [#962](https://github.com/gitlabform/gitlabform/pull/962) ([amimas](https://github.com/amimas))
As per the referenced issue [#533](https://github.com/gitlabform/gitlabform/issues/533), if there are multiple CI CD variables with same key/name but scoped to different "environment", gitlabform does not make the API call correctly. As a result, the variable cannot be deleted and an error is returned.

Bug fix includes a large refactor to use python-gitlab code and tidy up redundant paths, hence being included as part of v5 Release Candidate testing.

Thanks to all the contributors of this release!

## 4.8.0

### Refactors

* migrate project security settings to python-gitlab [#1152](https://github.com/gitlabform/gitlabform/pull/1152). [thomascizeron](https://github.com/thomascizeron))

### Documentation

* add deprecation warning for saml_group_links [#1168](https://github.com/gitlabform/gitlabform/pull/1168). ([amimas](https://github.com/amimas))
* fix broken ordered list formatting [#1174](https://github.com/gitlabform/gitlabform/pull/1174). ([brlin-tw](https://github.com/brlin-tw))

### Style

* Apply black v26 formatting [#1176](https://github.com/gitlabform/gitlabform/pull/1176). ([amimas](https://github.com/amimas))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 4.7.0

### Features

* Allow configuring any options supported by python-gitlab API client [#1140](https://github.com/gitlabform/gitlabform/pull/1140), [#1151](https://github.com/gitlabform/gitlabform/pull/1151). ([thomascizeron](https://github.com/thomascizeron))
* Allow configuring `max_retries`, `retry_transient_errors` and `backoff_factor` for legacy Gitlab API client [#1154](https://github.com/gitlabform/gitlabform/pull/1154). ([thomascizeron](https://github.com/thomascizeron))
* Add support for configuring push/remote mirrors [#1157](https://github.com/gitlabform/gitlabform/pull/1157). ([amimas](https://github.com/amimas))

### Bug Fixes

* Handle 403 Forbidden error when updating files in protected branches [#1163](https://github.com/gitlabform/gitlabform/pull/1163). ([amimas](https://github.com/amimas))
* Handle 403 Forbidden error when editing files in archived projects [#1163](https://github.com/gitlabform/gitlabform/pull/1163). ([amimas](https://github.com/amimas))

### Tests

* Fix group push rule test assertion [#1142](https://github.com/gitlabform/gitlabform/pull/1142). ([amimas](https://github.com/amimas))
* Fix tests for GitLab 18.8 instance enforcement on job token scope [#1163](https://github.com/gitlabform/gitlabform/pull/1163). ([amimas](https://github.com/amimas))

### Documentation

* Fix broken ordered list formatting in documentation [#1134](https://github.com/gitlabform/gitlabform/pull/1134). ([brlin-tw](https://github.com/brlin-tw))
* Improve documentation for gitlab client configuration [#1156](https://github.com/gitlabform/gitlabform/pull/1156). ([thomascizeron](https://github.com/thomascizeron))
* Add Ströer Online Marketing logo to "Used by" section [#1157](https://github.com/gitlabform/gitlabform/pull/1157). ([lociii](https://github.com/lociii))

### Chores

* Suppress false positive bandit warning for private_token [#1163](https://github.com/gitlabform/gitlabform/pull/1163). ([amimas](https://github.com/amimas))

## 4.6.1

### Bug Fixes

* Correct protecting branches error message [#1122](https://github.com/gitlabform/gitlabform/pull/1122). ([rickbrouwer](https://github.com/rickbrouwer))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!


## 4.6.0

### Features

* Add support for `duo_features_enabled` at `project_settings` level [#1113](https://github.com/gitlabform/gitlabform/pull/1113). ([TimKnight-DWP](https://github.com/TimKnight-DWP))

### Tests

* Fix project transfer tests for Gitlab 18.4 [#1116](https://github.com/gitlabform/gitlabform/pull/1116). ([Tim Knight](https://github.com/shoddyknight))

### Documentation

* Update `ci_cd_variables.md` to include raw variable example [#1091](https://github.com/gitlabform/gitlabform/pull/1091). ([uob-hillmu](https://github.com/uob-hillmu))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 4.5.0

### Features

* Add liquidlight logo [#1085](https://github.com/gitlabform/gitlabform/pull/1085). ([mikestreety](https://github.com/mikestreety))

### Documentation

* Update `ci_cd_variables.md` to include raw variable example [#1091](https://github.com/gitlabform/gitlabform/pull/1091). ([uob-hillmu](https://github.com/uob-hillmu))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 4.4.1

### Bug Fixes

* Group SAML Link config changes should be applied. Resolves [#994](https://github.com/gitlabform/gitlabform/issues/994), PR [#1076](https://github.com/gitlabform/gitlabform/pull/1076). ([amimas](https://github.com/amimas))

### Tests

* Improve branch protection tests [#1066](https://github.com/gitlabform/gitlabform/pull/1066). ([TimKnight-DWP](https://github.com/TimKnight-DWP))
* Add smoke tests for python 3.13
* Add acceptance test for group ldap links [#1079](https://github.com/gitlabform/gitlabform/pull/1079). ([amimas](https://github.com/amimas))

### Dependencies

* Update various dependencies to newer version.
* Update Dockerfile to use latest version of Alpine

Thanks to all the contributors of this release!

## 4.4.0

### Features

- implement "exclude-sections" CLI parameter [#1016](https://github.com/gitlabform/gitlabform/pull/1016). ([TimKnight-DWP](https://github.com/TimKnight-DWP))

### Documentation

- update intro using common term [#1065](https://github.com/gitlabform/gitlabform/pull/1065). ([mfriedenhagen](https://github.com/mfriedenhagen))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 4.3.0

### Chores

- Improve logging within group_members_processor [#1064](https://github.com/gitlabform/gitlabform/pull/1064) ([TimKnight-Opencast](https://github.com/TimKnight-Opencast))

### Features

- add support for group and project avatar [#987](https://github.com/gitlabform/gitlabform/pull/987) ([rickbrouwer](https://github.com/rickbrouwer))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 4.2.6

### Bug Fixes

* Handle the case where an integration doesn't exist when trying to delete it. (fixes #1036) [#1040](https://github.com/gitlabform/gitlabform/pull/1040) ([Andrew Wilkinson](https://github.com/andrewjw))
* Ensure gitlabform can handle mixed case username in gitlab [#1056](https://github.com/gitlabform/gitlabform/pull/1056) ([TimKnight-DWP](https://github.com/TimKnight-DWP))
* Verbose output for members_processor [#1018](https://github.com/gitlabform/gitlabform/pull/1018) ([BenediktBertsch](https://github.com/BenediktBertsch))
* Centred logos in `used by` documentation and added Roche [#1019](https://github.com/gitlabform/gitlabform/pull/1019) ([BenediktBertsch](https://github.com/BenediktBertsch))

### Tests

* fix test case for job token scope [#1035](https://github.com/gitlabform/gitlabform/pull/1035) ([amimas](https://github.com/amimas))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 4.2.5

### Fixes

* Do not attempt to create or update labels defined in parent group [#1007](https://github.com/gitlabform/gitlabform/pull/1007), closes [#1006](https://github.com/gitlabform/gitlabform/issues/1006), ([TimKnight-DWP](https://github.com/TimKnight-DWP))

Thanks to all the contributors of this release!


## 4.2.4

### Fixes

* Improves logging within labels processor [fdda773e](https://github.com/gitlabform/gitlabform/commit/fdda773e920dcb38680be2068cb5c0a7f64d92c8) ([TimKnight-DWP](https://github.com/TimKnight-DWP))

Thanks to all the contributors of this release!


## 4.2.3

### Fixes

* Fix labels get deleted and recreated if the key in YAML does not match the name in YAML or Gitlab [#1004](https://github.com/gitlabform/gitlabform/pull/1004) ([TimKnight-DWP](https://github.com/TimKnight-DWP))

Thanks to all the contributors of this release!

## 4.2.2

### Fixes

* Fix a 404 error when labels_processor attempts to delete labels set on parent group(s) [#1003](https://github.com/gitlabform/gitlabform/pull/1003), ([TimKnight-DWP](https://github.com/TimKnight-DWP))

Thanks to all the contributors of this release!


## 4.2.1

### Features

* add support for 'Planner' role [#981](https://github.com/gitlabform/gitlabform/pull/981) ([amimas](https://github.com/amimas))

### Fixes

* Improved logging in Labels processor [#1002](https://github.com/gitlabform/gitlabform/pull/1002), ([TimKnight-DWP](https://github.com/TimKnight-DWP))

### Documentation

* Document preference for using python-gitlab [#73](https://github.com/gitlabform/gitlabform/issues/73), [#988](https://github.com/gitlabform/gitlabform/pull/988) [gdubicki](https://github.com/gdubicki)
* Fix changelog for v4.2.0 [#982](https://github.com/gitlabform/gitlabform/pull/982) ([amimas](https://github.com/amimas))

### Dependencies

* Update various dependencies to newer version.


Thanks to all the contributors of this release!

## 4.2.0

### Features

* Add the possibility to add group level webhooks [#919](https://github.com/gitlabform/gitlabform/pull/919), [szEvEz](https://github.com/szEvEz)
* Add Project Security Settings support [#922](https://github.com/gitlabform/gitlabform/pull/922), [szEvEz](https://github.com/szEvEz)

### Tests

* Get rid of warnings about unregistered test markers [gdubicki](https://github.com/gdubicki)
* Handle flaky test in test_files [#961](https://github.com/gitlabform/gitlabform/pull/961), [gdubicki](https://github.com/gdubicki)
* Fix issues with eventual consistency in tests and cover an mr_approval_rules use case [#969](https://github.com/gitlabform/gitlabform/pull/969), [TimKnight-DWP](https://github.com/TimKnight-DWP)


### Documentation

* Improving the Features listings and local dev instructions, [gdubicki](https://github.com/gdubicki)
* Correct info on how to run a single test method [gdubicki](https://github.com/gdubicki)

### Code Style

* Implement `black` formatting [#959](https://github.com/gitlabform/gitlabform/pull/959), [gdubicki](https://github.com/gdubicki)

### Build / CI

* CI: separate steps of starting GitLab in Docker and running acceptance tests [gdubicki](https://github.com/gdubicki)
* Improved pyproject.toml [#945](https://github.com/gitlabform/gitlabform/pull/945), [gdubicki](https://github.com/gdubicki)
* Ensure that the app keeps running on MacOS and Windows [#958](https://github.com/gitlabform/gitlabform/pull/958), [gdubicki](https://github.com/gdubicki)

### Dependencies

* Update various dependencies to newer version.


Thanks to all the contributors of this release!

## 4.1.3

### Fixes

* fix: project topics should not be removed if topics are not in the config [#954](https://github.com/gitlabform/gitlabform/pull/954) ([amimas](https://github.com/amimas))

### Refactors

* refactor: migrate 'merge_requests_approvals' processor to python-gitlab [#955](https://github.com/gitlabform/gitlabform/pull/955) ([amimas](https://github.com/amimas))

### Build / CI

* chore(dev): add options in dev script to use gitlab-ce [#941](https://github.com/gitlabform/gitlabform/pull/941) ([@Jimisola](https://github.com/jimisola))
* chore: migrate project to pyproject.toml [#943](https://github.com/gitlabform/gitlabform/pull/943) ([Greg Dubicki](https://github.com/gdubicki))
* tests: stablize intermittent failure from TestFiles acceptance tests [#956](https://github.com/gitlabform/gitlabform/pull/956) ([amimas](https://github.com/amimas))

### Documentation

* docs: update v4.1.2 changelog [#947](https://github.com/gitlabform/gitlabform/pull/947) ([amimas](https://github.com/amimas))

### Dependencies

* Update various dependencies to newer version.


Thanks to all the contributors of this release!

## 4.1.2

### Features

* feat: Add enhanced support for managing project topics [#931](https://github.com/gitlabform/gitlabform/pull/931) ([@Jimisola](https://github.com/jimisola))

### Fixes

* fix: respect skip_groups when applying group configurations [#939](https://github.com/gitlabform/gitlabform/pull/939) ([rickbrouwer](https://github.com/rickbrouwer))

### Refactors

* refactor: update 'project_settings_processor' to use python-gitlab [#929](https://github.com/gitlabform/gitlabform/pull/929) ([amimas](https://github.com/amimas))

### Build

* chore: update base image to Alpine 3.21 [#930](https://github.com/gitlabform/gitlabform/pull/930) ([rroesch1](https://github.com/rroesch1))
* chore(ci): configure dependabot to group python-gitlab packages [#935](https://github.com/gitlabform/gitlabform/pull/935) ([amimas](https://github.com/amimas))

### Dependencies

* Update various dependencies to newer version.


Thanks to all the contributors of this release!

## 4.1.1

### Refactors

* refactor: migrate project push rules processor to python-gitlab [#923](https://github.com/gitlabform/gitlabform/pull/923) ([amimas](https://github.com/amimas)).
  - This PR refactors the processor used for managing project level push rules. The methods for managing this resource is removed and switched to use python-gitlab.

### Acceptance Tests

* test: add author email regex acceptance test [#924](https://github.com/gitlabform/gitlabform/pull/924) ([Tim Knight (DWP)](https://github.com/TimKnight-DWP)).

Thanks to all the contributors of this release!

## 4.1.0

### Features

* feat: add support for group push rules [#911](https://github.com/gitlabform/gitlabform/pull/911) ([szEvEz](https://github.com/szEvEz)).

### Refactors

* refactor: use python-gitlab when checking Bot user [#921](https://github.com/gitlabform/gitlabform/pull/921) ([Tim Knight (DWP)](https://github.com/TimKnight-DWP)).
  - means only one API call when enforcing members
  - fully cached
  - should remove exceptions for missing Users - as old REST api was throwing them too

Thanks to all the contributors of this release!

## 4.0.7

### Bug Fixes

* fix: remove caching on get_user_id_cached [#918](https://github.com/gitlabform/gitlabform/pull/918) ([Tim Knight (DWP)](https://github.com/TimKnight-DWP)).
  - the get user by username is already cached, so this reduces redundant data in the cache
  - adds extra logging to help users debug effectively

### Refactors

* refactor: do not throw exception from get_user_id [#918](https://github.com/gitlabform/gitlabform/pull/918) ([Tim Knight (DWP)](https://github.com/TimKnight-DWP)).
  - pass None up and let upstream throw exception if it wants

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 4.0.6

### Refactors

* use graphql to get member_roles to reduce permission level required [#915](https://github.com/gitlabform/gitlabform/pull/915), relates to [Gitlab Issue 511919](https://gitlab.com/gitlab-org/gitlab/-/issues/511919#note_2287581884) ([Tim Knight (DWP)](https://github.com/TimKnight-DWP)).
  - graph ql GET member_roles only needs Guest+ permissions
  - REST requires significantly higher permission sets which not all users maybe comfortable running with
  -  improve error handling and logging when users etc are not found

## 4.0.5

### Bug Fixes

* fix: gracefully handle "missing" Users when trying to remove from Project or Group [#913](https://github.com/gitlabform/gitlabform/pull/913), closes [#912](https://github.com/gitlabform/gitlabform/issues/912) ([Tim Knight (DWP)](https://github.com/TimKnight-DWP))

### Build Fixes

* test: mark 'TestVariables::test__builds_disabled' as skipped [#909](https://github.com/gitlabform/gitlabform/pull/909) ([amimas](https://github.com/amimas))
  ```
  GitLab API behaviour changed in current latest version (17.7.0) for listing project ci variables. 
  This is causing test failure and blocking changes from merging. The API changes do not have any breaking impact for gitlabform. 
  So, marking the currently failing test to be skipped. 
  It can be re-enabled again based on findings from the issue created in GitLab's backlog at https://gitlab.com/gitlab-org/gitlab/-/issues/511237
  ```

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 4.0.4

### Bug Fixes

* reduce unnecessary commits when modifying files [#892](https://github.com/gitlabform/gitlabform/pull/892), closes [#891](https://github.com/gitlabform/gitlabform/issues/891) ([Tim Knight (DWP)](https://github.com/TimKnight-DWP))
* wildcard based branch protection config fails to apply [#887](https://github.com/gitlabform/gitlabform/pull/887) ([KieranSt97](https://github.com/KieranSt97))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 4.0.3

### Performance

* Reduce execution time due to project members config [#885](https://github.com/gitlabform/gitlabform/pull/885) ([amimas](https://github.com/amimas))

### Documentation

* Fix Gitlab System hooks doc link [#883](https://github.com/gitlabform/gitlabform/pull/883) ([Philippe Granet](https://github.com/philippe-granet))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!


## 4.0.2

### Performance

* Reduce execution time of branch processor [#878](https://github.com/gitlabform/gitlabform/pull/878) ([amimas](https://github.com/amimas))

### Refactors

* Migrate branches processor to python-gitlab [#876](https://github.com/gitlabform/gitlabform/pull/876) ([amimas](https://github.com/amimas))
* Migrate files processor to python-gitlab [#874](https://github.com/gitlabform/gitlabform/pull/874) ([amimas](https://github.com/amimas))

### Build Process

* Fix codecov notification [8e89932](https://github.com/gitlabform/gitlabform/commit/8e89932d27c51001c1d04ca85c044797935532a5) ([Tim Knight (DWP)](https://github.com/TimKnight-DWP))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 4.0.1

### Bug Fixes

* fix: project settings failing to apply because membership config is not processed [#857](https://github.com/gitlabform/gitlabform/pull/857), closes [#765](https://github.com/gitlabform/gitlabform/issues/765). ([amimas](https://github.com/amimas))

## 4.0.0

### BREAKING CHANGES

- Stop supporting Python older than 3.12 [#789](https://github.com/gitlabform/gitlabform/pull/789), closes [#754](https://github.com/gitlabform/gitlabform/issues/754). ([Greg Dubicki](https://github.com/gdubicki)) 

### Dependencies

* Update various dependencies reliant on dropping python3.8 support; to newer version.

Thanks to all the contributors of this release!

## 3.16.5

### Dependencies

* Update various dependencies to newer version.

## 3.16.4

### Bug Fixes

* fix: print out to info level - user being processed [#864](https://github.com/gitlabform/gitlabform/pull/864), closes [#863](https://github.com/gitlabform/gitlabform/issues/863) ([Tim Knight (DWP)](https://github.com/TimKnight-DWP))

### Refactors

* refactor: migrate 'resource_groups' config to be managed by python-gitlab [#854](https://github.com/gitlabform/gitlabform/pull/854), closes [#628](https://github.com/gitlabform/gitlabform/issues/628) ([amimas](https://github.com/amimas))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 3.16.3

### Bug Fixes

* fix: only unprotect branch right before protecting again [#830](https://github.com/gitlabform/gitlabform/pull/830) ([Chris Hill](https://github.com/chrishill-1))
* fix: VariablesProcessor._print_diff() got an unexpected keyword argument 'diff_only_changed' [#852](https://github.com/gitlabform/gitlabform/pull/852), closes [#851](https://github.com/gitlabform/gitlabform/issues/851) ([kriko](https://github.com/kriko))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 3.16.2

### Bug Fixes

* fix: iterates through project list to check and add members [#843](https://github.com/gitlabform/gitlabform/pull/843). Resolves [836](https://github.com/gitlabform/gitlabform/issues/836). ([Sachin Kumar Singh](https://github.com/SachinKSingh28)) 

### Dependencies

* Update various dependencies to newer version.

## 3.16.1

### Bug Fixes

* fix: Adding members who already exist in project [#840](https://github.com/gitlabform/gitlabform/pull/840). Resolves [836](https://github.com/gitlabform/gitlabform/issues/836). ([Tim Knight (DWP)](https://github.com/TimKnight-DWP)) 

### Documentation

* fix "Edit a project webhook" Gitlab link [#839](https://github.com/gitlabform/gitlabform/pull/839) ([Philippe Granet](https://github.com/philippe-granet))

## 3.16.0

### Features

* Run gitlabform for a single group and all it's subgroups [#828](https://github.com/gitlabform/gitlabform/pull/828), closes [613](https://github.com/gitlabform/gitlabform/issues/613). ([Patrick Del Conte](https://github.com/exaV))

### Bug Fixes

* return all members when listing for member processor [#838](https://github.com/gitlabform/gitlabform/pull/838) ([Jack Hindley](https://github.com/jackhindleydwp))
* fix error when --diff-only-changed is set, but no changes are present [#833](https://github.com/gitlabform/gitlabform/pull/833) ([Arden Shackelford](https://github.com/Shackelford-Arden))
* remove 'enforce' key from the config so that it's not treated as a "variable" [#831](https://github.com/gitlabform/gitlabform/pull/831) ([Philippe Granet](https://github.com/philippe-granet))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 3.15.0

### Features

* Add flag to only print settings that are being changed [#815](https://github.com/gitlabform/gitlabform/pull/814) ([Arden Shackelford](https://github.com/Shackelford-Arden))

### Bug Fixes

* Idempotent updating for SAML Group Links [#824](https://github.com/gitlabform/gitlabform/pull/824) ([ItsJustMagic](https://github.com/ItsJustMagic))

### Refactors

* Moving members and members_processor to use python-gitlab [#822](https://github.com/gitlabform/gitlabform/pull/822) ([Arden Shackelford](https://github.com/Shackelford-Arden))

### Build Process

* Switch to Trusted Publishing to PyPi [#805](https://github.com/gitlabform/gitlabform/pull/805) ([Greg Dubicki](https://github.com/gdubicki))
* Cleanup tests to avoid multiple issue tracking integrations being enabled [#820](https://github.com/gitlabform/gitlabform/pull/820) ([Arden Shackelford](https://github.com/Shackelford-Arden))

### Documentation

* Add new feature docs to navigation of docs about various configuration options [#812](https://github.com/gitlabform/gitlabform/pull/812) ([amimas](https://github.com/amimas))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 3.14.1

### Features

* Enhanced cron expressions for scheduled pipelines. PRs [#800](https://github.com/gitlabform/gitlabform/pull/800), [801](https://github.com/gitlabform/gitlabform/pull/801), implements [#455](https://github.com/gitlabform/gitlabform/issues/455). ([Mirko Friedenhagen](https://github.com/mfriedenhagen))
* Show dry-run mode in the output header, if set. PR [#798](https://github.com/gitlabform/gitlabform/pull/798). ([Sebastian Gumprich](https://github.com/rndmh3ro))

### Build Process

* Remove grafana from test GitLab instance. ([Tim Knight (DWP)](https://github.com/TimKnight-DWP))
* Stop running setup.py directly, it's deprecated. ([Greg Dubicki](https://github.com/gdubicki))

### Dependencies

* Update various dependencies to newer version.

Thanks to all the contributors of this release!

## 3.14.0

(Not released because of a build issue, ugh.)

## 3.13.2

### Bug fixes

* Fix custom roles for GitLab SaaS users. PR [#787](https://github.com/gitlabform/gitlabform/pull/787). ([Tim Knight (DWP)](https://github.com/TimKnight-DWP))

### Dependencies

* Update packaging, cryptography, pytest, types-request, coverage and python-gitlab to newer versions.

## 3.13.1

### Bug fixes

* Fix documentation to publish website

## 3.13.0

### Features

* Add support for setting custom roles (Ultimate only) in project and group members. Creation of custom roles in gitlabform is **NOT SUPPORTED**. [#673](https://github.com/gitlabform/gitlabform/issues/673). PR [759](https://github.com/gitlabform/gitlabform/pull/759), [775](https://github.com/gitlabform/gitlabform/pull/775). ([Tim Knight (DWP)](https://github.com/TimKnight-DWP))

### Documentation

* Add info about and link to pyenv PR [#774](https://github.com/gitlabform/gitlabform/pull/774), ([Jimisola Laursen](https://github.com/jimisola))

### Build Process

* Improvements to codecov reports [43adfb9b](https://github.com/gitlabform/gitlabform/commit/43adfb9b9109d8c90a801787c3c533453642b617). ([Tim Knight (DWP)](https://github.com/TimKnight-DWP))
* Fixes to PRs workflows to ensure tests/linters run on branch. [7cd1bfc3](https://github.com/gitlabform/gitlabform/commit/7cd1bfc334761e7efaa61306bd421209e3ca2d69) & [c373b54](https://github.com/gitlabform/gitlabform/commit/c373b54f91f6f8cf12a8d3b73bd24cf3d04e9606). ([Tim Knight (DWP)](https://github.com/TimKnight-DWP))
* Adds suite of Acceptance Tests using Ultimate License. [d33b0928](https://github.com/gitlabform/gitlabform/commit/c836c86f9e857d79af0434ad74a7a5943319f8b0). ([Tim Knight (DWP)](https://github.com/TimKnight-DWP))

### Dependencies

* Update certifi, coverage, requests, types-requests to newer versions.

Thanks to all the contributors of this release!

## 3.12.0

### Features

* support for group SAML links, closes [#549](https://github.com/gitlabform/gitlabform/issues/549), PR [#760](https://github.com/gitlabform/gitlabform/pull/760) ([mahadevan-karthi-dwp](https://github.com/mahadevan-karthi-dwp))
* support for CI/CD Job Token Scope [#571](https://github.com/gitlabform/gitlabform/issues/571), PR [#758](https://github.com/gitlabform/gitlabform/pull/758) ([Tim Knight (DWP)](https://github.com/TimKnight-DWP))

### Dependencies

* Update py-test, python-gitlab, dependencies to newer version.

Thanks to all the contributors of this release!

## [3.11.1](https://github.com/gitlabform/gitlabform/compare/v3.11.0...v3.11.1) (2024-05-16)


### Bug Fixes

* release process and deploy container to GHCR ([741ff75](https://github.com/gitlabform/gitlabform/commit/741ff751fc26f17ccaca51fd8212175e7657839b))

## [3.11.0](https://github.com/gitlabform/gitlabform/compare/v3.10.0...v3.11.0) (2024-05-15)


### Features

* add option to not fail if configured resource group does not exist ([#650](https://github.com/gitlabform/gitlabform/issues/650)) ([a362d8e](https://github.com/gitlabform/gitlabform/commit/a362d8e41f9b65d2debd86e529d5939cc023dbbe)), closes [#649](https://github.com/gitlabform/gitlabform/issues/649)
* manage Project and Group Labels via gitlabform ([#751](https://github.com/gitlabform/gitlabform/issues/751)) ([f1be42b](https://github.com/gitlabform/gitlabform/commit/f1be42bd245237f512ff61de9dfb30057bdf1700))
* use python lib for group settings ([#746](https://github.com/gitlabform/gitlabform/issues/746)) ([03ce3fa](https://github.com/gitlabform/gitlabform/commit/03ce3faf0b01cbda4ff5f9137030a8f2ac159bb0))


### Documentation

* add fixes info into changelog for release 3.10.0 ([96a39ee](https://github.com/gitlabform/gitlabform/commit/96a39eee118b6c7e00d6dd1d47d845213876ffb3))
* move commit message guideline ([c0d3f68](https://github.com/gitlabform/gitlabform/commit/c0d3f68255fb13eb2a769d7df4a6888ffdcc742d))

## 3.10.0

### Features

* Add support for Application Settings [#120](https://github.com/gitlabform/gitlabform/issues/120), PR [#742](https://github.com/gitlabform/gitlabform/pull/742) ([Tim Knight (DWP)](https://github.com/TimKnight-DWP))

### Refactors

* Use new convenience methods for getting groups and projects in more places and document them in the contribution docs: PRs [#734](https://github.com/gitlabform/gitlabform/pull/734), [#743](https://github.com/gitlabform/gitlabform/pull/743) ([Tim Knight (DWP)](https://github.com/TimKnight-DWP))

### Dependencies

* Update some dependencies to newer version.

Thanks to all the contributors of this release!

## 3.9.7

### Fixes

* Processing group fails if it has more than 20 members [#732](https://github.com/gitlabform/gitlabform/issue/732), PR [#735](https://github.com/gitlabform/gitlabform/pull/735) ([Sachin Kumar Singh ](https://github.com/SachinKSingh28))

Thanks to all the contributors of this release!

## 3.9.6

### Fixes

* Process all schedules and not only the first 20 [#731](https://github.com/gitlabform/gitlabform/pull/731) ([Andreas Wirooks](https://github.com/nudgegoonies))

Thanks to all the contributors of this release!

## 3.9.5

### Fixes

* Error when running with `--noop` and `--output-file` parameter and config contains project to be transferred [#729](https://github.com/gitlabform/gitlabform/pull/729) ([long-wan-ep](https://github.com/long-wan-ep))

### Refactors

* Migrate `schedules` (pipeline schedules) configuration to use python-gitlab library [#706](https://github.com/gitlabform/gitlabform/pull/706) ([TimKnight-Opencast](https://github.com/TimKnight-Opencast))
* Migrate `group_members` configuration to use python-gitlab library [#697](https://github.com/gitlabform/gitlabform/pull/697) ([TimKnight-DWP](https://github.com/TimKnight-DWP))

Thanks to all the contributors of this release!

## 3.9.4

### Fixes

* Dry run failure when project transfer is configured along with other additional configs [#726](https://github.com/gitlabform/gitlabform/pull/726) ([long-wan-ep](https://github.com/long-wan-ep))

### Chores

* Update badge in project readme [commit](https://github.com/gitlabform/gitlabform/commit/30f199893118941adb86dccba2ee30441ffa8625) ([gdubicki](https://github.com/gitlabform/gitlabform/commits?author=gdubicki))

### Dependencies

* Update some dependencies to newer version.

Thanks to all the contributors of this release!

## 3.9.3

### Fixes

* Run app from Docker as non-root [#719](https://github.com/gitlabform/gitlabform/pull/719) ([lkwg82](https://github.com/lkwg82))

### Dependencies

* Update some dependencies to newer version.

Thanks to all the contributors of this release!

## 3.9.2

### Fixes

* Transfer project not working when target is ALL or ALL_DEFINED or group or subgroup [#714](https://github.com/gitlabform/gitlabform/pull/714) ([long-wan-ep](https://github.com/long-wan-ep))

### Documentation

* Fix branches keyword in MR approval rules [#710](https://github.com/gitlabform/gitlabform/pull/710) ([tmeijn](https://github.com/tmeijn))

### Dependencies

* Update some dependencies to newer version.

Thanks to all the contributors of this release!

## 3.9.1

### Fixes

* Hooks processing fails when config includes token [#693](https://github.com/gitlabform/gitlabform/pull/693) ([amimas](https://github.com/amimas))

### CI

* Install setuptools in github workflow to fix release process [commit](https://github.com/gitlabform/gitlabform/commit/b3eb1648ff18ecd2db799007341986378f0c4d6a) ([amimas](https://github.com/amimas))

### Dependencies

* Update some dependencies to newer version.

Thanks to all the contributors of this release!

## 3.9.0

### Features

* Ability to transfer projects between groups or namespaces [#582](https://github.com/gitlabform/gitlabform/pull/582) ([amimas](https://github.com/amimas))
* Add support for Python 3.12 and update to alpine 3.18 [#612](https://github.com/gitlabform/gitlabform/pull/612) ([gdubicki](https://github.com/gitlabform/gitlabform/commits?author=gdubicki))
* Add `enforce` support for project hooks/webhooks configuration [#664](https://github.com/gitlabform/gitlabform/pull/664)([TigreModerata](https://github.com/TigreModerata))

### Fixes

* JSON data with dates not serialized correctly [#656](https://github.com/gitlabform/gitlabform/pull/656) ([HontoNoRoger](https://github.com/HontoNoRoger))

### Refactors

* Migrate `archive` configuration to use python-gitlab library [#622](https://github.com/gitlabform/gitlabform/pull/622) ([amimas](https://github.com/amimas))
* Migrate `hooks` configuration feature to use python-gitlab library [#635](https://github.com/gitlabform/gitlabform/pull/635) ([TigreModerata](https://github.com/TigreModerata))
* Migrate `tags` configuration to use python-gitlab library [#642](https://github.com/gitlabform/gitlabform/pull/642) ([lhokktyn](https://github.com/lhokktyn))

### Documentation

* Clarify gitlabform release procedure steps [#600](https://github.com/gitlabform/gitlabform/pull/600) ([amimas](https://github.com/amimas))
* Add users' logs to the repo to fix problems with diplaying them [commit](https://github.com/gitlabform/gitlabform/commit/a8f7c6ca5f5f09344eb9887f5ab3fbec0c66cba4) ([gdubicki](https://github.com/gitlabform/gitlabform/commits?author=gdubicki))
* Fix broken links to references in homepage [#653](https://github.com/gitlabform/gitlabform/pull/653) ([alamirault](https://github.com/alamirault))

### Dependencies

* Update many dependencies to newer version.

### Styles

* Update formats using latest version of `black` (v24.1.1) [#681](https://github.com/gitlabform/gitlabform/pull/681) ([amimas](https://github.com/amimas))

Thanks to all the contributors of this release!

## 3.8.0

* **Add `allowed_to_create` support for tag protection**. PR [#551](https://github.com/gitlabform/gitlabform/pull/551), implements [#505](https://github.com/gitlabform/gitlabform/issues/505).
* **Require Python version >= 3.8** (as 3.7 is EOL since June 2023) and update dependencies that have required it. PR [#592](https://github.com/gitlabform/gitlabform/pull/592), implements [#576](https://github.com/gitlabform/gitlabform/issues/576).
* **Usernames in projects and groups should be case-insensitive**. PR [#556](https://github.com/gitlabform/gitlabform/pull/556), implements [#555](https://github.com/gitlabform/gitlabform/issues/555).
* Update many dependencies to newer version.
* Various fixes to local dev, tests, and CI of gitlabform.

Thanks to the contributors of this release::

* [amimas](https://github.com/amimas)
* [J4Numbers](https://github.com/J4Numbers)
* [gdubicki](https://github.com/gdubicki)

## 3.7.0

* **Add `enforce` support to managing pipeline schedules**. PR [#561](https://github.com/gitlabform/gitlabform/pull/561), implements [#539](https://github.com/gitlabform/gitlabform/issues/539).
* Fix group membership failing to apply when using `keep_bots` attribute. PR [#554](https://github.com/gitlabform/gitlabform/pull/554), fixes [#553](https://github.com/gitlabform/gitlabform/issues/553).

Thanks to the contributors of this release:

* [amimas](https://github.com/amimas)
* [Sachin Kumar Singh](https://github.com/SachinKSingh28)

## 3.6.1

* Fix acceptance tests after GitLab v16 started to require expiration date for all the tokens. PR [#557](https://github.com/gitlabform/gitlabform/pull/557) and [d2b0c81](https://github.com/gitlabform/gitlabform/commit/d2b0c8182b4e12c9aec1e0dc3b83e1c06c2fe3d8).
* Dependencies update.

Thanks to [amimas](https://github.com/amimas) for his contribution!

## 3.6.0

* **Enforcing project and group members while keeping the bot users is now easier.** When using `enforce: true` add also `keep_bots: true` at the same level. See [the docs](https://gitlabform.github.io/gitlabform/reference/members/) for more info. Implements [#454](https://github.com/gitlabform/gitlabform/issues/454), PR [#544](https://github.com/gitlabform/gitlabform/pull/544).
* (For contributors) All acceptance tests have been rewritten to use [python-gitlab](https://python-gitlab.readthedocs.io/en/stable/index.html) as a first step towards moving the whole project to use it instead of own home-grown library for the GitLab API. PR [#442](https://github.com/gitlabform/gitlabform/pull/442).

BIG thanks the contributions of this release:

* [Nejc Habjan](https://github.com/nejch) for his enormous work on migrating the tests to python-gitlab,
* [James Gauld](https://github.com/lhokktyn) for brilliantly implementing `keep_bots: true`,
* [Rajas Gujarathi](https://github.com/RajasGujarathi) for multiple improvements to the docs,
* [Waldek Maleska](https://github.com/weakcamel) for contribution to docs.

## 3.5.0

* **Make running with `ALL` work fast when using gitlab.com or a self-hosted GitLab instance and a non-admin account.** With a non-admin account the app will not try to get all the groups and projects, but only the ones where the used account has at least a Reporter role, which is the lowest level of permissions that allow to make a configuration change. Fixes [#509](https://github.com/gitlabform/gitlabform/issues/509), PR [#518](https://github.com/gitlabform/gitlabform/pull/518).
* Improved contribution docs. PR [#515](https://github.com/gitlabform/gitlabform/pull/515).

Thanks to [Mirko Friedenhagen](https://github.com/mfriedenhagen) for his contribution!

## 3.4.3

* Fix: add missing support for using group name when protecting an environment. Fixes [#503](https://github.com/gitlabform/gitlabform/issues/503), PR [#506](https://github.com/gitlabform/gitlabform/pull/506). 

## 3.4.2

* Improve the reliability in some cases (PR [#497](https://github.com/gitlabform/gitlabform/pull/497)):
  * retrying the whole section for a given entity (f.e. `files` for a project `foo/bar`) when it fails on a non-retryable individual HTTP request,
  * retrying individual HTTP requests on errors that may be returned by gitlab.com's CloudFlare CDN (520-531).

## 3.4.1

* Fix for old merge request syntax using inheritance when a sole `approvals_before_merge` setting is inherited/overwritten. PR [#481](https://github.com/gitlabform/gitlabform/pull/481).

## 3.4.0

* **Add support for [multiple merge request approval rules](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/rules.html#add-multiple-approval-rules) and for changing the name of the currently managed single approval rule**. Implements [#388](https://github.com/gitlabform/gitlabform/issues/388) and [#95](https://github.com/gitlabform/gitlabform/issues/95), PR [#435](https://github.com/gitlabform/gitlabform/pull/435) and many more.
* A more user-friendly error message when a key is not found. PR [#422](https://github.com/gitlabform/gitlabform/pull/422)
* Start to edit instead of remove+re-add users as project and group members when changing their access level or expiration time. This should give cleaner audit logs of membership changes and may resolve some issues. Related to issue [#466](https://github.com/gitlabform/gitlabform/issues/466), PR [#469](https://github.com/gitlabform/gitlabform/pull/469).
* Operate on simple dicts and lists instead of more complex ordereddict and CommentedSeq for easier to understand debug output and tests.
* Show the config before and after the internal transformation stage, with the debug output enabled.
* (For contributors) Big refactoring to make the code more logically groupped and contribution documentation updates for easier contributions. Please see the commit messages in the PR [#431](https://github.com/gitlabform/gitlabform/pull/431) for more information.

Thanks to the following contributors of this release:

* [Waldek Maleska](https://github.com/weakcamel), [amimas](https://github.com/amimas), [Jimisola Laursen](https://github.com/jimisola), [Siythrun](https://github.com/Siythrun) for consulting and testing of the multiple merge request approval rules feature, 
* [Rafael Zanella](https://github.com/zanella) for the development.

## 3.4.0rc4

* Fix internal conversion of group names and usernames to ids in some cases for Merge Request approval rules. Reported by [Siythrun](https://github.com/Siythrun) in issue [#388](https://github.com/gitlabform/gitlabform/issues/388), PR [#467](https://github.com/gitlabform/gitlabform/pull/467).
* Operate on simple dicts and lists instead of more complex ordereddict and CommentedSeq for easier to understand debug output and tests.
* Show the config before and after the internal transformation stage, with the debug output enabled.

## 3.3.4

* Fix unnecessary reapply of branch protection when `*_access_levels` is set to `0`. PR [#474](https://github.com/gitlabform/gitlabform/pull/474)

Thanks to [Ben Kuhar](https://github.com/BenKuhar) for his contribution!

## 3.4.0rc3

* Start to edit instead of remove+re-add users as project and group members when changing their access level or expiration time. This should give cleaner audit logs of membership changes and may resolve some issues. Related to issue [#466](https://github.com/gitlabform/gitlabform/issues/466), PR [#469](https://github.com/gitlabform/gitlabform/pull/469).

## 3.3.3

* Fix bug on the first run when both adding project members and the same users as merge request approvers. Fixes [#461](https://github.com/gitlabform/gitlabform/issues/461).

## 3.4.0rc2

* A more user-friendly error message when a key is not found. PR [#422](https://github.com/gitlabform/gitlabform/pull/422)
* Fix for converting legacy merge request approval into the new setup. PR [#456](https://github.com/gitlabform/gitlabform/pull/456)

Thanks to [Rafael Zanella](https://github.com/zanella) for his contribution!

## 3.3.2

* Don't strip trailing new lines from files. Fixes [#451](https://github.com/gitlabform/gitlabform/issues/451), PR [#452](https://github.com/gitlabform/gitlabform/pull/452).

## 3.3.1

* Fix for setting deploy key in some cases fail with HTTP 400: `{"fingerprint":["has already been taken"]}`. Fixes [#19](https://github.com/gitlabform/gitlabform/issues/19), PR [#441](https://github.com/gitlabform/gitlabform/pull/441).

## 3.4.0rc1

* **Add support for [multiple merge request approval rules](https://docs.gitlab.com/ee/user/project/merge_requests/approvals/rules.html#add-multiple-approval-rules) and for changing the name of the currently managed single approval rule**. Implements [#388](https://github.com/gitlabform/gitlabform/issues/388) and [#95](https://github.com/gitlabform/gitlabform/issues/95), PR [#435](https://github.com/gitlabform/gitlabform/pull/435). The syntax for this feature is shown [here](https://github.com/gitlabform/gitlabform/issues/388#issuecomment-1278213194) for now - it will be moved to the GitHub Pages docs before the final release of v3.4.0.
* (For contributors) Big refactoring to make the code more logically groupped and contribution documentation updates for easier contributions. Please see the commit messages in the PR [#431](https://github.com/gitlabform/gitlabform/pull/431) for more information.

## 3.3.0

* **Add support for managing project [Protected environments](https://docs.gitlab.com/ee/ci/environments/protected_environments.html#protected-environments).** PR [#423](https://github.com/gitlabform/gitlabform/pull/423) & PR [#430](https://github.com/gitlabform/gitlabform/pull/430)
* Add support for Python 3.11 and switch to this version in the Docker image.
* (For contributors) Move all the GitLabForm tests that require GitLab Premium license into a separate module and introduce a new GitHub Actions flow to enable running them for PRs after the maintainer's approval.

Thanks to [Rafael Zanella](https://github.com/zanella) for his contributions!

## 3.2.0

* **Add authoritative mode (`enforce: true`) support to group badges, group LDAP links, group variables, badges, deploy keys, variables.** Implements [#403](https://github.com/gitlabform/gitlabform/issues/403), PR [#419](https://github.com/gitlabform/gitlabform/pull/419).

## 3.1.2

* Make setting project-level CI/CI variables with a non-default different `environment_scope` work again. Fixes [#411](https://github.com/gitlabform/gitlabform/issues/411), PR [#414](https://github.com/gitlabform/gitlabform/pull/414).

## 3.1.1

* Fixed error when passing the GitLab token in the config file with single or double quotes. Fixes [#401](https://github.com/gitlabform/gitlabform/issues/401), PR [#412](https://github.com/gitlabform/gitlabform/pull/412).

## 3.1.0

* **Add support for Resource groups**. Implements [#341](https://github.com/gitlabform/gitlabform/issues/341). PR [#369](https://github.com/gitlabform/gitlabform/pull/369).
* Fix Integrations documentation. PR [#402](https://github.com/gitlabform/gitlabform/pull/402).  

Thanks to [@ep-linden](https://github.com/ep-linden) from [Elastic Path](https://www.elasticpath.com/) and to [@L154x](https://github.com/L154x) for their contribution!

## 3.0.0

This is a major new version with some backward incompatibility. Please follow [the upgrade guide](https://gitlabform.github.io/gitlabform/upgrade/) for a fast and safe upgrade.

New features/bugfixes:

* **Subgroups now _do_ inherit the settings from their groups.** It should have worked like this already, but it did not because of a [bug #372](https://github.com/gitlabform/gitlabform/issues/372) fixed in [PR #385](https://github.com/gitlabform/gitlabform/pull/385). (Please use `inherit: false` to keep the old behavior. See [the upgrade guide](https://gitlabform.github.io/gitlabform/upgrade/) for more info.),
* **Shorter and easier to read errors** (full stacktrace shown only when `--debug` is enabled),

Backward-incompatible maintenance changes:

* **Require GitLab version >= 14.4** (released in Oct 2021) as it contains the [required API rename](https://gitlab.com/gitlab-org/gitlab/-/issues/334500),
* **Require Python version >= 3.7** (as 3.6 is EOL since Dec 2021) and update many dependencies that have required it,
* **Drop support for a lot of deprecated configuration syntax** that the app has warned about: 
    * branch protection - no more `developers_can_push`, `developers_can_merge`, use `push_access_level`, `merge_access_level` etc. instead,
    * group members - no more `group_shared_with`, `enforce_group_members`, `group_access_level`, use `group_members`, `group_members.enforce`, `group_access` instead,
    * services/integrations - no more `recreate`,
* **Rename some configuration sections** following the renames made in GitLab:
    * `services` -> `integrations`,
    * `secret_variables` -> `variables`,
    * `group_secret_variables` -> `group_variables`,
* Drop the Debian-based Docker image (it's practically unused - you can maintain your own, if you needed it),
* _(For users of this app as a library)_ Rename some API methods, remove deprecated ones:
    * `protect_branch()` is now the method using the new API, the method using the old one has been removed,
    * `branch_code_owner_approval_required()` -> `set_branch_code_owner_approval_required()`.
    * `delete_legacy_approvers()` has been removed,
    * all the methods with `service(s)`/`secret_variable(s)`/`group_secret_variable(s)` in their names have been renamed to contain `integration(s)`/`variable(s)`/`group_variables(s)`.

Thanks to the contributors of this release: [@ep-linden](https://github.com/ep-linden) from [Elastic Path](https://www.elasticpath.com/).

## 2.12.0

* Update base Docker images:
    * from Python 3.9 and Alpine 3.14 to Python 3.10 and Alpine 3.16,
    * from Python 3.9 and Debian 10 (Buster) to Python 3.10 and Debian 11 (Bullseye).
* Fix Group CI/CD Variables not honoring `protected` and `masked` values set to `false`. Fixes [#384](https://github.com/gitlabform/gitlabform/issues/384).

## 2.11.1post3

* Moved the project from `gitlabform/gitlabform` to `gitlabform/gitlabform`. Stopped publishing new images to the old `egnyte/gitlabform` Docker registry.

## 2.11.1

* Fix another case of GitLab's Schedules API change/bug. Fixes [#364](https://github.com/gitlabform/gitlabform/issues/364).

## 2.11.0

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

## 2.10.1

* Fix a problem causing some changes to not be applied. Fixes [#334](https://github.com/gitlabform/gitlabform/issues/334). PR [#350](https://github.com/gitlabform/gitlabform/pull/350).

## 2.10.0

* **Deleting deploy keys is now possible**. This partially implements [#193](https://github.com/gitlabform/gitlabform/issues/193). Also completely replace the implementation of deploy keys, secret variables and group secret variables with a new universal one. This possibly fixes [#19](https://github.com/gitlabform/gitlabform/issues/19).
* **Up to 40% faster thanks to making less requests to GitLab.** (For almost 1000 repositories the apply time has dropped from ~18 minutes to ~11 minutes.)
* With debug enabled a lot less duplication and a more readable output of dicts (shown as JSONs).
* **For Contributors** Introduce `SingleEntityProcessor` that generalizes editing things that are single per project, f.e. settings or push rules set. It does not edit entities if there are not changes to be applied. Using it implementing new features can be superfast! (See also `MultipleEntitiesProcessor` added in v2.2.0).
* **For Contributors** Faster tests and improved usage of fixtures.

(A pre-release of 2.9.2 RC1 contained some of the above changes. 2.10.0rc1 pre-release was the same as 2.10.0 final but with a slightly different changelog - the speed gains turned out to be higher than expected.)

## 2.9.1

* Fix version 2.9.0 not even starting. 🤦‍♂️ Add test to prevent this from happening again.

## 2.9.0

* **Access level names (not only their numbers) are now accepted in the configuration**.
* More strictness in parsing configuration YAML and better error messages thanks to a switch to different libraries. F.e. hash keys overwriting is not accepted anymore.
* Moved the project from `egnyte/gitlabform` to `gitlabform/gitlabform` and switch to GitHub Registry as the new main Docker registry.

## 2.8.1

* Don't show "Warning: Using group_shared_with: is deprecated" although the user is not really using this config syntax.

## 2.8.0

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

## 2.7.1

* Speed up running for `ALL_DEFINED`, when the defined groups and projects for just a small part of all the GitLab instance's groups and projects. Additionally **always** show the number of omitted groups and projects for any reasons (no config, archived, skipped). Fixes [#285](https://github.com/gitlabform/gitlabform/issues/285).

## 2.7.0

* **Allow processing only requested configuration sections** using a new cli argument `-os / --only-sections`.
* Minimize the number of unnecessary audit branch unprotect/protect events. Up to now every apply of the `files` section for protected branch resulted in unprotect and then (re)protect event for each protected branches and each file. Now this will only happen when the user running GitLabForm actually needs to do that, which should not happen often if you are using an admin account. Completely fixes [#178](https://github.com/gitlabform/gitlabform/issues/178).

## 2.6.0

* **Complete support for Protected branches - access levels / users / groups allowed to push/merge/unprotect** (**GitLab Premium (paid) only**). PR [#289](https://github.com/gitlabform/gitlabform/pull/289).
* **Add option to allow push force in protected branches**. Implements [#227](https://github.com/gitlabform/gitlabform/issues/227).
* Fix a bug causing the app to get HTTP 502 from GitLab when protecting branches in some cases.
* Fix getting members list to include usernames of all direct members not just the first page. PR [#284](https://github.com/gitlabform/gitlabform/pull/284).

Big thanks to the contributors of this release: [@trissanen](https://github.com/trissanen)

## 2.5.0

* **Make commit messages for file operations configurable.** Implements [#278](https://github.com/gitlabform/gitlabform/issues/278).

Thanks to [@aleung](https://github.com/aleung) for his contribution!

## 2.4.0

* **Add wildcard support for `skip_groups` and `skip_projects`.** Implements [#275](https://github.com/gitlabform/gitlabform/issues/275) and [#276](https://github.com/gitlabform/gitlabform/issues/276).

Thanks to [@chris-workingmouse](https://github.com/chris-workingmouse) for his contribution!

## 2.3.0

* **Add Protected branches - users allowed to push/merge** (**GitLab Premium (paid) only**), PR [#273](https://github.com/gitlabform/gitlabform/pull/273).
* For `ALL_DEFINED` also skip archived projects even if they are explicitly defined in the config, unless -a flag is added - for consistency.
* **For Contributors** Add docs for running the test themselves in a Docker container and for running GitLab in Docker using a license file, for testing paid-only features.

Thanks to [@florentio](https://github.com/florentio), [@barryib](https://github.com/barryib) and [@Pigueiras](https://github.com/Pigueiras) for their contribution!

## 2.2.0

* **Add LDAP Group Links support** (**GitLab Premium (paid) only**). Implements [#140](https://github.com/gitlabform/gitlabform/issues/140).

* **Add project and group badges support**. Implements [#59](https://github.com/gitlabform/gitlabform/issues/59).

* Allow 0 (no access) in Protected Tags. Fixes [#172](https://github.com/gitlabform/gitlabform/issues/172).

* Exit on configuration missing `projects_and_groups` key. This will provide a helpful error message for typos made in this key. Fixes [#242](https://github.com/gitlabform/gitlabform/issues/242).
* Make error messages more friendly when there is no network connection or when configuration is invalid (f.e. YAML parsing errors).
* Make the output of some processors a bit more consistent.

* Fix detecting an "empty effective config" and improve the UI related to processing groups and projects with such. Fixes [#251](https://github.com/gitlabform/gitlabform/issues/251).

* Big refactoring that should make adding new features easier and faster. The main change is introducing a new way to implement "processors" - thanks to a generalized `MultipleEntitiesProcessor` class adding a new feature like Project Badges should is now as easy as implementing a class like `BadgesProcessor` and writing an acceptance test like `TestBadges`. Note that this new design may change in the near future and we are open to discussions and PRs to make it even better! We also plan to create a similar generalized `SingleEntityProcessor` class soon.

* Change the User Agent that the app uses when making requests to GitLab to a custom `GitLabForm/<gitlabform_version> (python-requests/<requests_version>)`.

## 2.1.2

* Managing project members is not incredibly slow anymore. Fixes [#240](https://github.com/gitlabform/gitlabform/issues/240)

Thanks to [@andrewjw](https://github.com/andrewjw) (Ocado Technology) for his contribution!

## 2.1.1

* Fixed sharing group with a subgroup. Fixes [#236](https://github.com/gitlabform/gitlabform/issues/236)
* Improved re-protecting branches after updating files in them. Fail fast if the config is invalid.
* Better Docker images:
    * Updated Alpine from 3.12 to 3.14,
    * Started to build images in ARM64 architecture (apart from x86-64),
    * Started to add tags <major_version>, <major_version>.<minor_version>. Note that Alpine-based image is the main one which gets these tags. For Debian-based images add "-buster" suffix. Implements [#173](https://github.com/gitlabform/gitlabform/issues/173)

Thanks to [@andrewjw](https://github.com/andrewjw) (Ocado Technology) for his contribution!

## 2.1.0

* **Added a feature to share groups with other groups, with optional enforcing.** Implements [#150](https://github.com/gitlabform/gitlabform/issues/150)

Thanks to [@andrewjw](https://github.com/andrewjw) (Ocado Technology) for this contribution!

## 2.0.6

* Fixed incorrect subgroups list when requesting to process ALL_DEFINED. Completes the fix for [#221](https://github.com/gitlabform/gitlabform/issues/221)

## 2.0.5

* *Really* fixed issue with `unprotect_branch_new_api`. Fixes [#219](https://github.com/gitlabform/gitlabform/issues/219)
* Fixed call to a Merge Requests Approvers API endpoint removed in GitLab 13.11.0. Fixes [#220](https://github.com/gitlabform/gitlabform/issues/220)
* Fixed potential security issue by enabling autoescaping when loading Jinja templates. (Bandit security tool issue [B701](https://bandit.readthedocs.io/en/latest/plugins/b701_jinja2_autoescape_false.html))

Thanks to [@Pigueiras](https://github.com/Pigueiras) for his contribution!

## 2.0.4

* Fixed issue with Push Rules when the project name contains a dot. Fixes [#224](https://github.com/gitlabform/gitlabform/issues/224)
* Fixed calling to process a single subgroup (like: `gitlabform 'group/subgroup'`). Fixes [#221](https://github.com/gitlabform/gitlabform/issues/221)

## 2.0.3

* Fixed issue with dry-run for Project Push Rules when the current config is empty (`None`). Fixes [#223](https://github.com/gitlabform/gitlabform/issues/223)

## 2.0.2

* Fixed issue with `unprotect_branch_new_api`. Fixes [#219](https://github.com/gitlabform/gitlabform/issues/219)
    (update: later it turned out that it was not really fixed in 2.0.2 but in 2.0.5 instead)

## 2.0.1

* Fixed issues with Jinja loader.
* Fixed calls to GitLab API that do not contain 'x-total-pages' header (gradually rolled out since [GitLab MR #23931](https://gitlab.com/gitlab-org/gitlab-foss/-/merge_requests/23931)).
* Start showing deprecation warning when using the old branch protection API config syntax.

Thanks to [@mkjmdski](https://github.com/mkjmdski) for his contribution!

(2.0.0post1-3 release is technically the same as 2.0.1 but was incorrectly versioned.)

## 2.0.0

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

## before 2.0.0

Please see [GitHub pre-2.0 releases' descriptions](https://github.com/gitlabform/gitlabform/releases?after=v2.0.0rc1).
