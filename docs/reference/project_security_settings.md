# Project Security Settings

!!! info

    This section requires GitLab Ultimate (paid). (This is a GitLab's limitation, not GitLabForm's.)

This section purpose is to manage project security settings, especially [secret push protection](https://docs.gitlab.com/ee/user/application_security/secret_detection/secret_push_protection/#enable-secret-push-protection).

On Gitlab Dedicated and Self-managed instances, you must [allow secret push
protection](https://docs.gitlab.com/ee/user/application_security/secret_detection/secret_push_protection/#allow-the-use-of-secret-push-protection-in-your-gitlab-instance) before you can enable it in a project

Values are documented at [LDAP Group Links section of the Groups API docs](https://docs.gitlab.com/ee/api/project_security_settings.html#update-pre_receive_secret_detection_enabled-setting).

## Example

```yaml
projects_and_groups:
  group_1/project_1:
    project_security_settings:
      pre_receive_secret_detection_enabled: true
```
