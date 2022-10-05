# Badges

## Project Badges

This section purpose is to manage the [project badges](https://docs.gitlab.com/ee/user/project/badges.html#project-badges).


Key names here are just any labels, except if the key name is `enforce` and is set to `true` - then only the badges defined here will remain in the project, all other will be deleted.


The values are as documented at [add a badge to a project endpoint](https://docs.gitlab.com/ee/api/project_badges.html#add-a-badge-to-a-project), with the appropriate [placeholder tokens](https://docs.gitlab.com/ee/api/project_badges.html#placeholder-tokens), but we **require** you to define the `name` of the badge.
If the only non-required value is `delete: true` then the given badge is going to be removed.

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    badges:
      coverage:
        name: "Coverage"
        link_url: "http://example.com/ci_status.svg?project=%{project_path}&ref=%{default_branch}"
        image_url: "https://shields.io/my/badge"
      old-badge-to-delete:
        name: "a-badge"
        delete: true
      enforce: true # optional
```

## Group Badges

This section purpose is to manage the [group badges](https://docs.gitlab.com/ee/user/project/badges.html#group-badges).


Key names here are just any labels, except if the key name is `enforce` and is set to `true` - then only the badges defined here will remain in the group, all other will be deleted.


The values are as documented at [add a badge to a group endpoint](https://docs.gitlab.com/ee/api/group_badges.html#add-a-badge-to-a-group), with the appropriate [placeholder tokens](https://docs.gitlab.com/ee/api/group_badges.html#placeholder-tokens), but we **require** you to define the `name` of the badge.
If the only non-required value is `delete: true` then the given badge is going to be removed.

Example:

```yaml
projects_and_groups:
  group_1/*:
    group_badges:
      group-pipeline-status:
        name: "Group Badge"
        link_url: "https://gitlab.yourcompany.com/%{project_path}/-/commits/%{default_branch}"
        image_url: "https://gitlab.yourcompany.com/%{project_path}/badges/%{default_branch}/pipeline.svg"
      enforce: true # optional
```
