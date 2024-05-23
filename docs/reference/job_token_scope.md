# CI/CD job token scope

## Project CI/CD job token scope
This section purpose is to manage the [project CI/CD job token scope](https://docs.gitlab.com/ee/ci/jobs/ci_job_token.html#control-job-token-access-to-your-project)


The values are like documented at [Job Token Scope API docs](https://docs.gitlab.com/ee/api/project_job_token_scopes.html), **except the Enabled**.

We use `limit_access_to_this_project` as the variable name for restricting access to the Project from other projects, rather than `inbound_enabled` in the GET and `enabled` in the PATCH requests defined in the api, in line with GitLab's UI and [intended language](https://docs.gitlab.com/ee/update/deprecations.html#default-cicd-job-token-ci_job_token-scope-changed-1).

You can:

* [Limit access to a project](https://docs.gitlab.com/ee/api/project_job_token_scopes.html#patch-a-projects-cicd-job-token-access-settings)
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