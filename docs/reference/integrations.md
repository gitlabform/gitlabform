# Integrations

This section purpose is to manage the [project integrations](https://docs.gitlab.com/ee/integration/).

The keys name are as in the endpoints described in the [GitLab Integrations API docs](https://docs.gitlab.com/ee/api/integrations.html), f.e. `pipelines-email`, `jira` etc.

The values are like the params for a given integration, as described in the same doc OR a single special value `delete: true` causing the given integration to be removed.

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    services:
      slack:
        delete: true
      drone-ci:
        delete: true
      jira:
        active: true
        url: https://jira.yourcompany.com
        username: foo # this is required by this integration, even if it's not used
        password: bar # this is required by this integration, even if it's not used
```
