# Push mirrors (Remote mirrors)

This section allows to manage **[push mirroring](https://docs.gitlab.com/ee/user/project/repository/mirror/push.html)** for projects.

## Basic use

All mirrors are defined under the `remote_mirrors` section/key. Multiple mirrors can be defined as a dictionary. The key name for each mirror is the **mirror target URL** (e.g., `https://...` or `ssh://...`) and the values are parameters described in the **[Remote mirrors API docs](https://docs.gitlab.com/ee/api/remote_mirrors.html#create-a-new-push-mirror)**.

Also, GitLab's UI doesn't allow updating configuration of an existing mirror. One must be deleted and recreated. But, using GitLab's edit API, GitLabForm will modify an existing mirror, if changes to mirror attributes are detected.

```yaml
projects_and_groups:
  my-group/my-project:
    remote_mirrors:
      "https://username:password@example.com/path-to/my-repo.git":
        enabled: true
        auth_method: "password"
        only_protected_branches: true
```

## Authentication and URL formats

Unlike the GitLab Web UI, which provides separate fields for usernames and passwords, GitLab API expects authentication credentials to be embedded directly within the URL string. For more details on how GitLab handles mirror authentication, see the [GitLab documention on Authentication methods for mirrors](https://docs.gitlab.com/user/project/repository/mirror/#authentication-methods-for-mirrors).

The URL Patterns are not clearly documented in GitLab's API documentation. Below are some example URL format:

| Protocol | `auth_method` | URL Format |
| --- | --- | --- |
| HTTPS (Token) | `password` | `https://username:token@github.com/org/repo.git` |
| SSH (Password) | `password` | `ssh://username:password@external-host.com/org/repo.git` |
| SSH (Public Key) | `ssh_public_key` | `ssh://git@external-host.com/org/repo.git` |

!!! tip "Verify your URL format"

    If you are unsure of the exact URL format GitLab expects for a specific provider, manually create a mirror in the GitLab UI first and make sure it works. Then, use a `curl` command to inspect the resulting mirror object:
    
    ```bash
    curl --header "PRIVATE-TOKEN: <your_token>" "https://gitlab.example.com/api/v4/projects/<id>/remote_mirrors
    ```
    
    Note that GitLab will return the URL with credentials masked (e.g., `https://*****:*****@...`), but the structure will confirm if your URL for GitLabForm configuration is correct.

### Limitation

For SSH type mirrors, GitLab requires host key of the target where the mirror is located. GitLab's Web UI allows it to either automatically detect the target host using the mirror URL or a host key can be manually entered.

As of GitLab 18.6, the API does not accept the target's SSH host keys in the request payload. Because of this, SSH based mirror can be configured using GitLabForm, but it will not be functional. GitLab will not be able to push to the target mirror. And unlike the API, GitLab's UI doesn't allow "editing" a mirror either where manual intervention could've been a work-around.

!!! warning

    Configuring a SSH based mirror using GitLabForm is possible but it will not be functional due to limitation with GitLab's API not accepting mirror's host key.

    !!! tip

        Use an HTTP based mirror for completely automatied configuration-as-code workflow for managing push mirrors.

## Special configuration keys

### `enforce`

This is a boolean type key that can be set under `remote_mirrors` section. Set to `true` to delete any mirrors found in GitLab that are not defined in the config.

```yaml
projects_and_groups:
  my-group/my-project:
    remote_mirrors:
      enforce: true # Delete all other mirrors in GitLab that are not defined below
      "https://username:password@example.com/path-to/my-repo.git":
        enabled: true
        auth_method: "password"
        only_protected_branches: true
```

### `print_details`

Because repository mirror settings are often restricted to users with Maintainer or Owner permissions, regular developers often cannot verify if a mirror is functioning correctly through the GitLab Web UI.

Set this attribute to true and GitLabForm will retrieve the full state of all remote mirrors in the project and print their attributes to the terminal. This includes the synchronization status, last successful update time, and any error messages returned by GitLab. This is particularly useful in CI/CD logs to monitor the health of your mirrors.

```yaml
projects_and_groups:
  my-group/my-project:
    remote_mirrors:
      print_details: true # Global option to report on all mirrors in this project
      "https://username:password@example.com/path-to/my-repo.git":
        enabled: true
        auth_method: "password"
```

Example Output in Terminal:

```
📋 Final Remote Mirror Report for 'my-group/my-project':
  ────────────────────────────────────────
  - enabled: True
  - auth_method: password
  - enabled: True
  - host_keys: []
  - id: 479
  - keep_divergent_refs: None
  - last_error: None
  - last_successful_update_at: 2026-01-11T10:00:00.000Z
  - last_update_at: None
  - last_update_started_at: None
  - mirror_branch_regex: None
  - only_protected_branches: False
  - update_status: ✅ finished
  - url: https://*****:*****@example.com/path-to/my-repo.git
  ────────────────────────────────────────
```

### `delete`

This is a boolean type key that can be used within indiviudal mirror. Set this to `true` for the corresponding mirror to be deleted.

```yaml
projects_and_groups:
  my-group/my-project:
    remote_mirrors:
      # Mirror to GitHub using a Personal Access Token (HTTPS)
      "https://username:github_pat_12345@github.com/my-org/my-repo.git":
        enabled: true
        only_protected_branches: true
        keep_divergent_refs: false
      # Delete an old mirror
      "https://username:password@example.com/path-to/my-repo.git":
        delete: true
```

### `force_push`

Set this to `true` within a mirror to trigger an immediate push to the remote mirror.

```yaml
projects_and_groups:
  my-group/my-project:
    remote_mirrors:
      "https://username:password@example.com/path-to/my-repo.git":
        enabled: true
        auth_method: "password"
        only_protected_branches: true
        force_push: true       # Sync immediately after configuration
```

### `force_update`

For each mirror, GitLabForm will compare all parameters between the config and what's in GitLab. If changes are detected or has drifted from the config, the mirror configuration in GitLab will be updated.

However, GitLabForm cannot detect changes to authentication, as GitLab returns credentials in the URL as masked. Set this key to `true`, in case credentials need to be changed for a mirror. For example: change username/password. Note, changing the rest of URL (i.e. protocol, path, etc.) will result in a new mirror to be created.

```yaml hl_lines="4"
projects_and_groups:
  my-group/my-project:
    remote_mirrors:
      "https://{--username--}{++new_username++}:{--password--}{++new_password++}@example.com/path-to/my-repo.git":
        enabled: true
        auth_method: "password"
        only_protected_branches: true
        force_update: true  # Update the existing mirror with new credentials based on config above
```

!!! tip "Only use when needed"

    Using this key will result in the mirror being updated **always**. For performance reason, remove this configuration if mirror authentication/credential update is not needed. This will avoid unnecessary API calls to GitLab.


### `print_public_key`

If a mirror is configured that is SSH type and `auth_method` is set to `ssh_public_key`, GitLab will automatically create a public key. This key will need to be setup in the target system so that GitLab can authenticate and push to the target. In this case, you need a way to retrieve this public key. Set this attribute to `true` and GitLabForm will retrieve the key and print it in the terminal.

```yaml
projects_and_groups:
  my-group/my-project:
    remote_mirrors:
      "ssh://git@external-provider.com/repo.git":
        enabled: true
        auth_method: "ssh_public_key"
        print_public_key: true # Prints the key so you can add it to the target
```
