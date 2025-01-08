# Merge Requests

!!! info

    This section requires GitLab Premium (paid). (This is a GitLab's limitation, not GitLabForm's.)

!!! new

    The syntax described below has been introduced in v3.4.0 of GitLabForm. The old syntax, that used to be documented here,
    will still supported until the release of v4.* of GitLabForm, but is deprecated and you should migrate to the new one.

## Project

These sections' purpose is to manage the project-Level Merge Requests **configuration** and **rules**.

### Configuration

The section `merge_requests_approvals` keys are as documented at GitLab's [project-level Merge Request approvals API, change configuration](https://docs.gitlab.com/ee/api/merge_request_approvals.html#change-configuration).

Note that under it the deprecated key `approvals_before_merge` is NOT allowed in GitLabForm - please use the `approvals_required` field in the specific rules instead (see below.)

!!! note

    Some Merge Requests-related settings are also set in the [project settings](settings.md#project-settings).

### Rules

In the `merge_requests_approval_rules` section, key names are just any labels, except if the key name is `enforce` and is set to `true` - then only the rules defined here will remain in the project, all other will be deleted.

Under each key the contents are as documented at GitLab's [project-level Merge Request approvals API, create project-level rule](https://docs.gitlab.com/ee/api/merge_request_approvals.html#create-project-level-rule), but additionally, you may use these keys:

* `users` - an array of usernames,
* `groups` - an array of group/subgroup paths,
* `protected_branches` - an array of branch names.

...instead of the built-in keys `user_ids`, `group_ids`, `protected_branch_ids` which require you to provide the internal ids of these entities.

!!! warning

    If any of the users or groups is not a member of the project, they cannot be approvers.
    However GitLab will NOT fail with an error in such case - it's will silently ignore these users and groups.
    This is GitLab's limitation, not GitLabForm's.

### Examples

Example 1 - a single approval rule where all the project members can approve, but no approval is required to merged the MR.

Note that `rule_type: any_approver` field makes it a special kind of rule where you don't have to reference specific users or groups. Also note that you can combine it with any number in `approvals_required` and any `name`.

```yaml
projects_and_groups:
  group_1/project_1:
    merge_requests_approvals:
      disable_overriding_approvers_per_merge_request: true
    merge_requests_approval_rules:
      any: # this is just a label
        approvals_required: 0
        name: "Any member"
        rule_type: any_approver
      enforce: true
```

Example 2 - a single approval rule that requires at least 2 approval from the following approvers: `user1`, `user2` and/or the members of the group `my-group` who will be called "Special approvers" in the GitLab's web UI:

```yaml
projects_and_groups:
  group_1/project_1:
    merge_requests_approvals:
      disable_overriding_approvers_per_merge_request: true
    merge_requests_approval_rules:
      default: # this is just a label
        approvals_required: 2
        name: "Special approvers"
        users:
          - user1
          - user2
        groups:
          - my-group
      enforce: true
```

Example 3 - two approval rules:

* one that requires at least 1 approval from any member of the `security-team` group, who will be called "Security Team" in the GitLab's web UI,
* second that requires at least 1 approval from any of the project members, who will be called "Any member" in the GitLab's web UI.

```yaml
projects_and_groups:
  group_1/project_1:
    merge_requests_approvals:
      disable_overriding_approvers_per_merge_request: true
    merge_requests_approval_rules:
      security: # this is just a label
        approvals_required: 1
        name: "Security Team"
        groups:
          - security-team
      any: # this is just a label
        approvals_required: 1
        name: "Any member"
        rule_type: any_approver
      enforce: true
```

Example 4 - two approval rules:

* one that requires at least 1 approval from `senior-sre-1` and/or `senior-sre-2`, who will be called "Senior SRE" in the GitLab's web UI, but this rule will apply only to MRs to the protected branches `production` and `staging`,
* second that requires at least 1 approval from any of the project members, who will be called "Any member" in the GitLab's web UI.

```yaml
projects_and_groups:
  group_1/project_1:
    merge_requests_approvals:
      disable_overriding_approvers_per_merge_request: true
    merge_requests_approval_rules:
      senior: # this is just a label
        approvals_required: 1
        name: "Senior SRE"
        users:
          - senior-sre-1
          - senior-sre-2
        protected_branches:
          - production
          - staging
      any: # this is just a label
        approvals_required: 1
        name: "Any member"
        rule_type: any_approver
      enforce: true
```

## Groups

These sections' purpose is to manage the group-Level Merge Requests **configuration** and **rules**.

### Configuration

The section `group_merge_requests_approval_settings` keys are as documented at GitLab's [Group MR approval settings](https://docs.gitlab.com/ee/api/merge_request_approval_settings.html#update-group-mr-approval-settings).

The section `group_merge_requests_approval_rules` keys are as documented at GitLab's [Create group-level approval rules](https://docs.gitlab.com/ee/api/merge_request_approvals.html#create-group-level-approval-rules).

**HINT** On self-managed GitLab, by default this feature is not available.
To make it available, an administrator can enable the feature flag named
`approval_group_rules`. On GitLab.com and GitLab Dedicated, this feature is not
available. This feature is not ready for production use.

### Examples

```yaml
projects_and_groups:
  group_1/project_1:
    group_merge_requests_approval_settings:
      retain_approvals_on_push: false
      allow_overrides_to_approver_list_per_merge_request: true
      allow_committer_approval: false
      allow_author_approval: false
      require_reauthentication_to_approve: true
    group_merge_requests_approval_rules:
      any:
        approvals_required: 1
        name: "Developer Approval"
        rule_type: any_approver
```
