# CI/CD job token scope

## Project CI/CD job token scope
This section's purpose is to manage the [project CI/CD job token scope](https://docs.gitlab.com/ee/ci/jobs/ci_job_token.html#control-job-token-access-to-your-project).

The GitLab UI refers to this setting under "Authorized groups and projects". This controls which projects can use CI/CD job tokens to authenticate with the current project.

There are two main options in the UI:
*   **All groups and projects**: This option disables any restrictions, allowing any project to use a job token to access this project. This corresponds to the API field `inbound_enabled` being `false`.
*   **Only this project and any groups and projects in the allowlist**: This option restricts access to only the current project and those explicitly added to the allowlist. This corresponds to the API field `inbound_enabled` being `true`.

It's important to note that this project-level setting can only be controlled if the instance-level setting `enforce_ci_inbound_job_token_scope_enabled` is disabled. This instance setting requires admin privileges to change.

In `gitlabform`, we use the `limit_access_to_this_project` setting to control the "Authorized groups and projects" option. Setting `limit_access_to_this_project: true` enables the restriction ("Only this project and any groups and projects in the allowlist"), while `limit_access_to_this_project: false` disables it ("All groups and projects").

The [Job Token Scope API docs](https://docs.gitlab.com/ee/api/project_job_token_scopes.html) use `inbound_enabled` in GET requests and `enabled` in PATCH requests, which can be confusing. The `gitlabform` `limit_access_to_this_project` setting maps to the API's `enabled` field in PATCH requests.

In addition to the main setting, you can manage the project's CI/CD job token allowlist. This allowlist determines which other projects and groups are authorized to use their job tokens to access this project when the "Only this project and any groups and projects in the allowlist" option is enabled.

Within the `allowlist` section of the configuration, you can use the `enforce` setting:

*   When `enforce: true` is set, `gitlabform` will ensure that the allowlist in GitLab exactly matches the `projects` and `groups` specified in your configuration. Any projects or groups found in the GitLab allowlist that are *not* listed in your `gitlabform` configuration will be removed.
*   If `enforce` is not set or set to `false`, `gitlabform` will only add the projects and groups specified in the configuration to the allowlist, leaving any existing entries in GitLab untouched.

You can add projects and groups to the allowlist using their ID or path/name:

* [Add other projects to the job token allowlist](https://docs.gitlab.com/ee/api/project_job_token_scopes.html#add-a-project-to-a-cicd-job-token-inbound-allowlist)
* [Add groups to the job token allowlist](https://docs.gitlab.com/ee/api/project_job_token_scopes.html#add-a-group-to-a-cicd-job-token-allowlist)

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    job_token_scope:
      limit_access_to_this_project: true
      allowlist:
        enforce: true # When enforce enabled, projects/groups set in GitLab but not in Config will be removed from allowlists
        projects:
          - 123 # Add by project ID
          - group-bar/project-foo # Add by Path/Name
        groups:
          - 5 # Add by group ID
          - group-bar # Add by Group Name (will include all sub-groups)
          - group-abc/subgroup-xyz # Add Subgroup 
```