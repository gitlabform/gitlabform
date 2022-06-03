# Group LDAP links

!!! info

    This section requires GitLab Premium (paid). (This is a GitLab's limitation, not GitLabForm's.)

This section purpose is to manage [group membership via LDAP](https://docs.gitlab.com/ee/user/group/index.html#manage-group-memberships-via-ldap).

The keys and values for each link should be as documented in the [LDAP Group Links section of the Groups API docs](https://docs.gitlab.com/ee/api/groups.html#add-ldap-group-link-with-cn-or-filter), **except the id**.

The `provider` key should contain a value that can be found in the GitLab web UI, here:

![group-ldap-links-provider.png](../images/group-ldap-links-provider.png)

\- it's "ldapmain" in this example.

The `access_level` should be set to one of the [valid access levels](https://docs.gitlab.com/ee/api/members.html#valid-access-levels).

Example:

```yaml
projects_and_groups:
  group_1/*:
    group_ldap_links: 
      devops_are_maintainers: # this is just a label
        provider: AD
        cn: devops
        group_access: maintainer
      app_devs_are_developers: # this is just a label
        provider: AD
        filter: "(employeeType=developer)"
        group_access: developer
```
