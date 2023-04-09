# Upgrading to new major versions

Some of these changes between major application versions may affect the effective configuration that would be applied if you run the application. Therefore to do the upgrade safely please follow this procedure.

## From 2.\* to 3.\*

Steps outline:

1. Update to the latest v2.x.x and **fix all the deprecation warnings the application prints out during run**. The syntax deprecated in v2 has been removed in v3.
2. Stop v2 from running automatically (if you have such automation).
3. In your config:

    * In v3 a bug that caused subgroup config to not inherit its group config has been fixed. If you do have configs for some groups and a config for their subgroups, then your effective configuration may change after the upgrade to v3. If you do not want that, or you are not sure, then please do the following to keep the old behavior: add `inherit: false` entries to all of such subgroups config, under each configuration section:
Example:
```yaml
projects_and_groups:
  some_group/*:
    group_settings:
      project_creation_level: maintainer
      subgroup_creation_level: owner
      visibility: internal
  
  some_group/subgroup/*:
    group_settings:
      # add the line below to keep the old behavior
      inherit: false
      project_creation_level: developer
        
  some_group/subgroup/subsubgroup/*:
    group_settings:
      # add the line below to keep the old behavior
      inherit: false
      visibility: private
```
    * Replace `services:` with `integrations:`,
    * Replace `secret_variables:` with `variables:`,
    * Replace `group_secret_variables:` with `group_variables:`,
    * Replace `config_version: 2` with `config_version: 3`
    * Update `merge_requests:`; `approvals_before_merge:` needs to be defined
      in specific approval rule
 
4. Upgrade the app from v2 to v3.
5. Re-enable v3 to run automatically (if you have such automation).

## From 1.\* to 2.\*

Steps outline:

1. Generate effective configuration that is applied when you run v1 and keep it. Update to >= v1.23.0 first, as we added the feature to output the effective config to file to that version. Add these parameters to your regular ones: `--output-file v1_configuration.yaml`. You may also add `-n` to run it in a noop mode. Save the generated YAML.
2. Stop v1 from running automatically (if you have such automation).
3. Upgrade to v2 and update the configuration syntax. The major syntax changes are:

    * add `config_version: 2`,
    * remove `api_version: 4`,
    * common, group and project configs are now all under a single `projects_and_groups` key,
    * if you have `common_settings` section then move it under a new key `"*"` under `projects_and_groups`,
    * if you have `groups_settings` or `projects_settings` then move their contents to be under all under `projects_and_groups`,
    * for each group config replace `<group name>:` with `<group name>/*:`.
    * leave project configs unchanged.
 
4. Generate effective configuration that is applied when you run v2 using "noop" mode. Add these parameters to your regular ones: `--output-file v2_configuration.yaml --noop --include-archived-projects`. (The last one is needed to have the projects list to process the same as for v1, as v2 by default skips the archived projects.) Save the generated YAML file.
5. Compare the YAML files with effective configuration from v1 to v2 and correct the configuration to get either exactly the same result or acceptable differences.
6. Run v2 without the "noop" mode and review the results. Look for failures and exit code different from 0. Fix found issues.
7. Re-enable v2 to run automatically (if you have such automation).
