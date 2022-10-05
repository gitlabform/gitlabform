# Merge Requests

!!! info

    This section requires GitLab Premium (paid). (This is a GitLab's limitation, not GitLabForm's.)

This section purpose is to manage the Merge Requests settings.


The settings under the `approvals` key are as documented at GitLab's [Merge Request approvals API](https://docs.gitlab.com/ee/api/merge_request_approvals.html#change-configuration).


The `approvers` and `approver_groups` are both optional. If any of these are set, GitLabForm starts to manage an approval rule named "Approvers (configured using GitLabForm)". Under the `approvers` there should be an array of usernames, under the `approver_groups` - array of group/subgroup paths.


The `remove_other_approval_rules` key is optional and if it is set to `true` then any other approval rules that might exist in the project, other than the one mentioned above, will be deleted.


!!! note

    Some Merge Requests-related settings are also set in the [project settings](settings.md#project-settings).

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    merge_requests:
      approvals:
        approvals_before_merge: 2
        reset_approvals_on_push: true
        disable_overriding_approvers_per_merge_request: true
      approvers:
        - user1
        - user2
      approver_groups:
        - my-group
        - my-group1/subgroup
        - my-group2/subgroup/subsubgroup
      remove_other_approval_rules: false
```
