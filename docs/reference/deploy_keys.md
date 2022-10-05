# Deploy keys

## Project deploy keys

This section purpose is to manage [project deploy keys](https://docs.gitlab.com/ee/user/project/deploy_keys/#create-a-project-deploy-key).


Key names here are just any labels, except if the key name is `enforce` and is set to `true` - then only the deploy keys defined here will remain in the project, all other will be deleted.


The values are as documented at [Deploy keys API docs](https://docs.gitlab.com/ee/api/deploy_keys.html#add-deploy-key), **except the id**.

Notes:

* you have to always provide the whole SSH key under the `key`. This is a limitation of the GitLab API. You can see an example of this [here in the docs](https://docs.gitlab.com/ee/api/deploy_keys.html#add-deploy-keys-to-multiple-projects).
* you can set the value of `can_push` only on the first assignment of the key or its creation. This is a limitation of the GitLab API. See [this issue and comment](https://gitlab.com/gitlab-org/gitlab-foss/-/issues/30021#note_39567845) for more information.

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    deploy_keys:
      # --- Adding/resetting
      a_friendly_deploy_key_name: # this is just a label
        key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDB2QKx6BPzL (...)"
        title: ssh_key_name_that_is_shown_in_gitlab
        can_push: false

      another_friendly_deploy_key_name:
        key: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDtbyEK66RXg (...)"
        title: other_ssh_key_name_that_is_shown_in_gitlab
        can_push: true

      # --- Deleting
      ensure_to_remove_this_one:
        title: different_key_title
        delete: true

      enforce: true # optional
```
