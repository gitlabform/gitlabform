# Deploy keys

## Project deploy keys

This section purpose is to manage the project deploy keys.

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    deploy_keys:
      # --- Adding/resetting
      # the below name is not used by GitLab, it's just for you
      a_friendly_deploy_key_name:
        # you have to pass the whole SSH key content here even if GitLab already has this key added,
        # and you just assign it to a given project. this is a limitation of the GitLab API.
        key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDB2QKx6BPzL (...)"
        title: ssh_key_name_that_is_shown_in_gitlab
        # note that you can set this to `true` or `false` ONLY on the first assignment of the key
        # or its creation. see https://gitlab.com/gitlab-org/gitlab-ce/issues/30021#note_39567845
        # this is a limitation of the GitLab API.
        can_push: false

      # the below name is not used by GitLab, it's just for you
      another_friendly_deploy_key_name:
        key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDtbyEK66RXg (...)"
        title: other_ssh_key_name_that_is_shown_in_gitlab
        can_push: true

      # --- Deleting
      # the below name is not used by GitLab, it's just for you
      ensure_to_remove_this_one:
        title: different_key_title
        delete: true
```
