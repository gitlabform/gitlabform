# Avatars

## Project Avatars

This section purpose is to manage the project avatar - the image that is displayed next to your project name in GitLab.


The value is a path to an image file relative to the directory where GitLabForm is run. If the value is explicitly set to "", the existing project avatar will be removed.

Example:
```
projects_and_groups:
  group_1/project_1:
    project:
      avatar: "images/project-logo.png"
```

To remove an avatar, set the value to "":

```
projects_and_groups:
  group_1/project_1:
    project:
      avatar: ""
```

## Group Avatars
This section purpose is to manage the group avatar - the image that is displayed next to your group name in GitLab.


The value is a path to an image file relative to the directory where GitLabForm is run. If the value is explicitly set to "", the  existing group avatar will be removed.

Example:
```
groups:
  group_1:
    group:
      avatar: "images/group-logo.png"
```

To remove an avatar, set the value to "":
```
groups:
  group_1:
    group:
      avatar: ""
```

## File Location

The image file path should be relative to the directory where GitLabForm is executed. For example, if GitLabForm is run from /home/user/gitlabform and the avatar path is set to `images/logo.png`, GitLabForm will look for the file at /home/user/gitlabform/images/logo.png.
