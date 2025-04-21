# Avatars

## Project Avatars

This section purpose is to manage the project avatar - the image that is displayed next to your project name in GitLab.

The value is a path to an image file. You can use both absolute paths and relative paths.

Example:
```
projects_and_groups:
  group_1/project_1:
    project_settings:
      avatar: "images/project-logo.png"
```

To remove an avatar:
```
projects_and_groups:
  group_1/project_1:
    project_settings:
      avatar: ""
```

## Group Avatars
This section purpose is to manage the group avatar - the image that is displayed next to your group name in GitLab.
The value is a path to an image file. You can use both absolute paths and relative paths.

Example:
```
groups:
  group_1:
    group_settings:
      avatar: "images/group-logo.png"
```

To remove an avatar:
```
groups:
  group_1:
    group_settings:
      avatar: ""
```
