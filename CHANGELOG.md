## Changelog

### 2.0.0 (final)

For a complete list of changes between v1 and v2 please read all the below entries for v2 RC*.

### 2.0.0 RC8

* Add support for Python 3.9

### 2.0.0 RC7

* Fixed diffing feature for secret variables

### 2.0.0 RC6

* Fix deep merging of configuration. Fixes [#209](https://github.com/egnyte/gitlabform/issues/209)

* Prevent multiple email notifications from being sent when adding members to project. Fixes [#101](https://github.com/egnyte/gitlabform/issues/101)

* Prevent project's Audit Events being filled in with "Added protected branch". Fixes [#178](https://github.com/egnyte/gitlabform/issues/178)

* Fixed using "expires_at" for users. Fixes [#207](https://github.com/egnyte/gitlabform/issues/207)

* Add diffing feature for secret variables (with values shown as hashes to protect the secrets from leaking).

* Fix diffing feature that did not really work for Python < 3.9.

Thanks to [@Pigueiras](https://github.com/Pigueiras) and [@YuraBeznos](https://github.com/YuraBeznos) for their contributions!

### 2.0.0 RC5

* **Make deep merging of configuration actually work (breaking change).** Fixes [#197](https://github.com/egnyte/gitlabform/issues/197)

* Start releasing pre-releases as Docker images. They have tags with specific versions, but not "latest" tag as it is reserved for new final releases. Implements [#201](https://github.com/egnyte/gitlabform/issues/201) 

* Added Windows support. Fixes [#206](https://github.com/egnyte/gitlabform/issues/206)

* Added checking for invalid syntax in "members" section. Defining groups or users directly under this key instead of under sub-keys "users" and "groups" will now trigger an immediate error.

Thanks to [@Pigueiras](https://github.com/Pigueiras) and [@weakcamel](https://github.com/weakcamel) for their contributions!

(2.0.0 RC4 was not completely released and therefore has been withdrawn.)

### 2.0.0 RC3

* Fixed the bug that caused RC2 to have noop and op modes switched... 🤦‍♂️

* (For Contributors) Make writing tests easier and the tests more robust. Deduplicate a lot of the boilerplate code, allow putting configs into the test methods and use pytest fixtures for easier setup and cleanup. This should fix issues with tests reported in [#190](https://github.com/egnyte/gitlabform/issues/190). Also stop storing any dockerized GitLab data permanently to avoid problems like [#196](https://github.com/egnyte/gitlabform/issues/196) and probably other related to failed dockerized GitLab upgrades.

* Rename "integration tests" to "acceptance tests". Because they ARE in fact acceptance tests.

Thanks to [@ss7548](https://github.com/ss7548) and [@houres](https://github.com/houres) for their contributions!

### 2.0.0 RC2

* **Ignore archived projects by default (breaking change).** You can restore the previous behavior by adding `--include-archived-projects`/`-a` command line switch. Note that you have to do it if you want to unarchive archived projects! Fixes [#157](https://github.com/egnyte/gitlabform/issues/157) in (arguably) a more convenient way.

* **Allow any case in groups and projects names (breaking change).** GitLab groups and projects names are case sensitive but you cannot create such entities that differ only in the case. There is also a distinction between a "name" and a "path" and they may differ in case... To make work with this easier GitLabForm now accepts any case for them in both config files as well as when provided as command line arguments. We also disallow such entities that differ only in case (f.e. `group/*` and `GROUP/*`) to avoid ambiguity. Fixes [#160](https://github.com/egnyte/gitlabform/issues/160).

### 2.0.0 RC1

(Compared to v1)

* **New config syntax (breaking change).** All 3 levels under a common key `groups_and_projects`. It should contain a dict, where common config is under a special `"*"` key, group configs under keys like `group/*` and project configs under keys like `group/project`. This will allow introducing pattern matching in these keys and introducing support for multiple config files in the future releases. Partially implements [#138](https://github.com/egnyte/gitlabform/pull/138).

* **Introduce config versioning (breaking change).** ...or rather a change to avoid breakage. New major releases of GitLabForm starting with v2 will look for `config_version` key in the config file. If it doesn't exist, or the version does not match expected then the app will exit to avoid applying unexpected configuration and allowing the user to update the configuration.

* **Exit with code != 0 when any group/project processing was failed (breaking change).** This will allow you to notice problems when running the app from CI. Note that you can restore the old behaviour by running the app with `(...) || true`. Fixes [#153](https://github.com/egnyte/gitlabform/issues/153).

* Standardized exit codes. Exit with 1 in case of input error (f.e. config file does not exist), with 2 in case of processing error (f.e. GitLab returns HTTP 500).

* New command line switch `--start-from-group`/`-sfg` allows starting to process groups from a given number (like projects with `--start-from`/`-sf`).

* Color output. Implements [#141](https://github.com/egnyte/gitlabform/issues/141).

* Remove the need to add the `gitlab.api_version` configuration key.

Thanks to [@amimas](https://github.com/amimas), [@weakcamel](https://github.com/weakcamel) and [@kowpatryk](https://github.com/kowpatryk) for their contributions!

### before 2.0.0 RC1

Please see [GitHub releases descriptions](https://github.com/egnyte/gitlabform/releases).
