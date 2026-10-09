# Pull mirror

This section allows to manage **[pull mirroring](https://docs.gitlab.com/user/project/repository/mirror/pull/)** for projects.

!!! info

    This functionality requires a GitLab Premium (paid) subscription and GitLab 17.6 or later, as it uses the dedicated **[Pull mirroring API](https://docs.gitlab.com/api/project_pull_mirroring/)**. Configuring pull mirroring through the project settings (the `mirror` and `import_url` attributes of the project edit API) is deprecated by GitLab and not supported by GitLabForm.

## Basic use

A project can have only one pull mirror, so the `pull_mirror` section is a flat map of settings. The parameters are described in the **[Pull mirroring API docs](https://docs.gitlab.com/api/project_pull_mirroring/#update-project-pull-mirroring-settings)**.

```yaml
projects_and_groups:
  my-group/my-project:
    pull_mirror:
      url: "https://username:token@example.com/some/repo.git"
      enabled: true
      only_mirror_protected_branches: false
```

## Authentication and URL formats

GitLab accepts credentials either embedded in the URL (`https://username:token@...`) or as the separate `auth_user` and `auth_password` attributes:

```yaml
projects_and_groups:
  my-group/my-project:
    pull_mirror:
      url: "https://example.com/some/repo.git"
      auth_user: "username"
      auth_password: "token"
      enabled: true
```

GitLab masks credentials in the mirror URL it returns (e.g., `https://*****:*****@...`) and never returns `auth_user`/`auth_password`. Because of this, GitLabForm cannot detect credential changes; use [`force_update`](#force_update) to apply them.

### Limitation

The Pull mirroring API only supports password/token based authentication. Pull mirrors that use **SSH with public key authentication** can only be configured through the GitLab web UI, as the API does not accept the target's SSH host keys nor manage the key pair.

!!! warning

    Also note that due to a GitLab issue, projects with an SSH based pull mirror configured in the UI may fail with `400: {'import_url': ["can't be blank"]}` on **any** project settings update through the API. If you hit this with the `project_settings` section, this is a GitLab bug, not something GitLabForm can work around.

## Removing a pull mirror

The API provides no way to delete a pull mirror configuration. To stop mirroring, disable it (if the project has no pull mirror, this configuration is skipped):

```yaml
projects_and_groups:
  my-group/my-project:
    pull_mirror:
      enabled: false
```

## Special configuration keys

### `force_pull`

Set this to `true` to trigger an immediate pull from the remote repository after the configuration is applied.

```yaml
projects_and_groups:
  my-group/my-project:
    pull_mirror:
      url: "https://username:token@example.com/some/repo.git"
      enabled: true
      force_pull: true       # Sync immediately after configuration
```

### `force_update`

GitLabForm compares all parameters between the config and what's in GitLab and only updates the mirror when changes are detected. However, GitLabForm cannot detect changes to authentication, as GitLab masks credentials. Set this key to `true` in case credentials need to be changed.

```yaml
projects_and_groups:
  my-group/my-project:
    pull_mirror:
      url: "https://username:new_token@example.com/some/repo.git"
      enabled: true
      force_update: true  # Update the existing mirror with new credentials based on config above
```

!!! tip "Only use when needed"

    Using this key will result in the mirror being updated **always**. For performance reason, remove this configuration if mirror authentication/credential update is not needed. This will avoid unnecessary API calls to GitLab.
