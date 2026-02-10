# Group SAML links

!!! info

    This section requires GitLab Premium (paid). (This is a GitLab's limitation, not GitLabForm's.)

This section purpose is to manage [group membership via SAML group links](https://docs.gitlab.com/ee/user/group/saml_sso/group_sync.html#configure-saml-group-links).

Key names here are just any labels.

Except if the key name is `enforce` and is set to `true` - then only the group SAML links defined here will remain in the group, all other will be deleted.

Values are like documented at [SAML Group Links section of the Groups API docs](https://docs.gitlab.com/ee/api/groups.html#saml-group-links), **except the id**.

The `saml_group_name` should be set to the SAML group name

The `access_level` should be set to one of the [valid access levels](https://docs.gitlab.com/ee/api/members.html#valid-access-levels).

Example:

```yaml
projects_and_groups:
  group_1/*:
    group_saml_links: 
      devops_are_maintainers: # this is just a label
        saml_group_name: devops
        access_level: maintainer
      developers_are_developers: # this is just a label
        saml_group_name: developers
        access_level: developer

      enforce: true # optional
```