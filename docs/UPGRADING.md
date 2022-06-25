# Upgrading to new major versions

## From 2.* to 3.*

No configuration update is required. Version 3 of this app uses the same configuration syntax as version 2.

You may, but you don't have to, update `config_version` value from `2` to `3`.

## From 1.* to 3.*

Some of these changes may affect the effective configuration that would be applied if you run the application. Therefore to do the upgrade safely please follow this procedure.

Version 2 of this app has introduced some breaking changes that may affect the effective configuration that would be applied if you run the application. Version 3 of the app contains the same changes. To perform the upgrade safely please follow the below procedure.

Steps outline:

1. Generate effective configuration that is applied when you run v1 and keep it. Update to >= v1.23.0 first, as we added the feature to output the effective config to file to that version. Add these parameters to your regular ones: `--output-file v1_configuration.yaml`. You may also add `-n` to run it in a noop mode. Save the generated YAML.
2. Stop v1 from running automatically (if you have such automation).
3. Upgrade to v3 and update the configuration syntax. The major syntax changes are:
* add `config_version: 3` (value `2` is accepted too),
* remove `api_version: 4`,
* common, group and project configs are now all under a single `projects_and_groups` key,
* if you have `common_settings` section then move it under a new key `"*"` under `projects_and_groups`,
* if you have `groups_settings` or `projects_settings` then move their contents to be under all under `projects_and_groups`,
* for each group config replace `<group name>:` with `<group name>/*:`.
* leave project configs unchanged.
4. Generate effective configuration that is applied when you run v3 using "noop" mode. Add these parameters to your regular ones: `--output-file v3_configuration.yaml --noop --include-archived-projects`. (The last one is needed to have the projects list to process the same as for v1, as v3 by default skips the archived projects.) Save the generated YAML file.
5. Compare the YAML files with effective configuration from v1 to v3 and correct the configuration to get either exactly the same result or acceptable differences.
6. Run v3 without the "noop" mode and review the results. Look for failures and exit code different from 0. Fix found issues.
7. Re-enable v3 to run automatically (if you have such automation).
