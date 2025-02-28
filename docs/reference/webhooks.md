# Webhooks

## Project Webhooks

This section purpose is to manage the [Webhooks](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html) (aka Project Hooks).

The key names here are webhook URLs, except if the key name is `enforce` and is set to `true` - in this case only the hooks defined here will remain in the project, all others will be deleted. When `enforce` is false, or not set, individual hooks can be deleted by setting their value to `delete: true`.
The other values of the URL keys are the parameters described at [edit a project webhook](https://docs.gitlab.com/ee/api/project_webhooks.html#edit-a-project-webhook), **except the id and hook_id**.

## Examples

Example 1: only the first hook will be deleted. Here, omitting the `enforce` key altogether achieves the same result.

```yaml
projects_and_groups:
  group_1/project_1:
    hooks:
      enforce: false
      "http://host.domain.com/some-old-hook-you-want-to-remove-from-config":
        delete: true
      "http://127.0.0.1:5000/hooks/merge_request":
        push_events: false # this is set to true by GitLab API by default
        merge_requests_events: true
        token: some_secret_auth_token
```

Example 2: here all hooks previously set in the `group_1/project_1` project will be removed, except `http://127.0.0.1:5000/hooks/merge-request` will remain.

```yaml
projects_and_groups:
  group_1/project_1:
    hooks:
      enforce: true
      "http://127.0.0.1:5000/hooks/merge-request":
        push_events: false
        merge_requests_events: true
```

Example 3: here `enforce: true` is applied to the hooks of all projects within `group-1`: for each of these the `example.hook.url` hook will be created/updated and all others will be removed, unless further specified - in `project-1` the `special-hook.net` hook will also be added/kept and all others deleted (so that `project-1` ends up with just these 2 hooks).

```yaml
group-1/*:
  hooks:
    enforce: true
    https://example.hook.url:
      push_events: true
group-1/project-1:
  hooks:
    https://special-hook.net:
      job_events: true
```

## Group Webhooks

This section purpose is to manage the
[Group Webhooks](https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#group-webhooks).

The key names here are webhook URLs, except if the key name is `enforce` and is
set to `true` - in this case only the hooks defined here will remain in the
group, all others will be deleted. When `enforce` is false, or not set,
individual hooks can be deleted by setting their value to `delete: true`.
The other values of the URL keys are the parameters described at
[edit a group webhook](https://docs.gitlab.com/ee/api/group_webhooks.html#edit-group-hook),
**except the id and hook_id**.

## Examples

```yaml
projects_and_groups:
  group-1/*:
    group_hooks:
      "http://127.0.0.1:5000/hooks/merge_request":
        push_events: false
        merge_requests_events: true
        token: some_secret_auth_token
```
