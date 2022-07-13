# Webhooks

This section purpose is to manage the [Webhooks](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html) (aka Project Hooks).

The key names here are webhook URLs and values are as parameters described at [edit project hooks endpoint](https://docs.gitlab.com/ee/api/projects.html#edit-project-hook), **except the id and hook_id**.

If the only value is `delete: true` then the given webhook is going to be removed.

Example:
```yaml
projects_and_groups:
  group_1/project_1:
    hooks:
      "http://host.domain.com/some-old-hook-you-want-to-remove-from-config":
        delete: true
      "http://127.0.0.1:5000/hooks/merge-request":
        push_events: false # this is set to true by GitLab API by default
        merge_requests_events: true
        token: some_secret_auth_token
```
