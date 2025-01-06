# Push rules

!!! info

    This section requires GitLab Premium (paid). (This is a GitLab's limitation, not GitLabForm's.)

## Group Push rules

This section purpose is to manage the [group push rules](https://docs.gitlab.com/ee/user/project/repository/push_rules.html).

The settings should be as documented at GitLab's [Push rules section of the Groups API docs](https://docs.gitlab.com/ee/api/group_push_rules.html#add-push-rules-to-a-group), **except the id**.

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    group_push_rules:
      commit_message_regex: '(.|\s)*\S(.|\s)*'
      member_check: false
      commit_committer_check: true
      commit_committer_name_check: true
```

## Project Push rules

This section purpose is to manage the [project push rules](https://docs.gitlab.com/ee/user/project/repository/push_rules.html#override-global-push-rules-per-project).

The settings should be as documented at GitLab's [Push rules section of the Projects API docs](https://docs.gitlab.com/ee/api/projects.html#add-project-push-rule), **except the id**.

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    project_push_rules:
      commit_message_regex: 'Fixes \d +'
      branch_name_regex: ""
      deny_delete_tag: false
      member_check: false
      prevent_secrets: false
      author_email_regex: ""
      file_name_regex: ""
      max_file_size: 0 # in MB, 0 means unlimited
```
