# Webhooks

This section purpose is to manage the [Webhooks](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html) (aka Project Hooks).

The key names here are webhook URLs, except if the key name is `enforce` and is set to `true` - in this case only the hooks defined here will remain in the project, all other will be deleted. Setting `enforce: false` is the same as omitting it, in which case only webhooks that have the value `delete: true` will be removed.
The other values of the URL keys are the parameters described at [edit project hooks endpoint](https://docs.gitlab.com/ee/api/projects.html#edit-project-hook), **except the id and hook_id**.

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
