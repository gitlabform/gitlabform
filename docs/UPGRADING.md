# Upgrading to new major versions

## From 1.* to 2.0

Version 2 has introduced some breaking changes that may affect the effective configuration that would be applied if you run the application. To make the change safely please follow this procedure.

Steps outline:

1. Generate effective configuration that is applied when you run v1 and keep it.
2. Stop v1 from running automatically (if you have such automation).
3. Upgrade to v2 and update the configuration syntax.
4. Generate effective configuration that is applied when you run v2 using "noop" mode.
5. Compare the effective configuration from v1 to v2 and correct the configuration to get either exactly the same result or acceptable differences.
6. Run v2 without the "noop" mode and review the results. Look for failures and exit code different from 0. Fix found issues.
7. Re-enable v2 to run automatically (if you have such automation).

Steps details:

= 1. Update to v1.23.0 as we added the feature to output the effective config to file to that version.
Add these parameters to your regular ones: `--output-file v1_configuration.yaml`. You may also add `-n` to run it in a noop mode.

= 3. The major syntax changes are:
* add `config_version: 2`,
* remove `api_version: 4`,
* common, group and project configs are now all under a single `projects_and_groups` key,
* if you have `common_settings` section then move it under a new key `"*"` under `projects_and_groups`,
* if you have `groups_settings` or `projects_settings` then move their contents to be under all under `projects_and_groups`,
* for each group config replace `<group name>:` with `<group name>/*:`.
* leave project configs unchanged.

= 4. Add these parameters to your regular ones: `--output-file v2_configuration.yaml --noop --include-archived-projects`.
(The last one is needed to have the projects list to process the same as for v1, as v2 by default skips the archived projects.)
