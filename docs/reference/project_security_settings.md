# Project Security Settings

!!! info

    This section requires GitLab Ultimate (paid). (This is a GitLab's limitation, not GitLabForm's.)

This section purpose is to manage project security settings, especially [secret push protection](https://docs.gitlab.com/ee/user/application_security/secret_detection/secret_push_protection/#enable-secret-push-protection).

On Gitlab Dedicated and Self-managed instances, you must [allow secret push
protection](https://docs.gitlab.com/ee/user/application_security/secret_detection/secret_push_protection/#allow-the-use-of-secret-push-protection-in-your-gitlab-instance) before you can enable it in a project

Values are documented at the [Project security settings API docs](https://docs.gitlab.com/api/project_security_settings/#update-the-secret_push_protection_enabled-setting).

!!! note

    This setting was renamed from `pre_receive_secret_detection_enabled` to `secret_push_protection_enabled` in GitLab 17.11.
    Use the new name `secret_push_protection_enabled`. Configs still using the old name will trigger a redundant
    update on every run, because the GitLab API only reports the setting under its new name.

## Example

```yaml
projects_and_groups:
  group_1/project_1:
    project_security_settings:
      secret_push_protection_enabled: true
```
