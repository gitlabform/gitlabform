# Webhooks

This section purpose is to manage the [Webhooks](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html) (aka Project Hooks).

The key names here are webhook URLs, except if the key name is `enforce` and is set to `true` - then only the hooks defined here will remain in the project, all other will be deleted.
The values of the URL keys are parameters described at [edit project hooks endpoint](https://docs.gitlab.com/ee/api/projects.html#edit-project-hook), **except the id and hook_id**.

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
      enforce: false
```
