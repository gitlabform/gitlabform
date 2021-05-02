## Changelog

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
