# Files

This section purpose is to manage files in the repository. Unlike other sections it does not correspond to any single GitLab API.

You can ensure that files with specific content ARE in the repo or that they ARE NOT in the repo, in specific branch or branches.

Each key in this section is a path to a file in the repo and the values are dicts with keys like:

* `overwrite` - if set to `false` and the file already exists, but has a different content, then it is not changed; default is `true`,
* `skip_ci` - if set to `true` then the changes to a given file will be done with commits that will not trigger the CI pipeline; default is `false`,
* `branches` - can be a single string `all`, string `protected` or an array of branch names,
* `only_first_branch` - if set to `true` then only the first branch from the list above that exists will be processed (unless you pass `--strict` as cli parameter to the app - then it will fail when trying to process a non-existent branch),
* `commit_message` - set this to a custom commit message that will be used by the app; optional,
* `content` - the literal contents that should be put into the target file; use this or `file`,
* `file` - the path to the file which content should be put into the target file; use this or `content`, both absolute and relative paths are supported,
* `template` - if set to `false` then simple templating feature will be disabled; default is `true` and `{{ project }}` will be replaced by the project name while `{{ group }}` by a group name,
* `jinja_env` - set this to a dict of key-values that will be used in the target file as a template,
* `delete` - if set to `true` then the target file will be deleted, not created.

Example 1 - initialize with a default README, if custom is not provided:

```yaml
projects_and_groups:
  group_1/project_1:
    files:
      "README.md":
        overwrite: false
        branches:
          - develop
        skip_ci: true
        content: |
          This is a default README. Please replace it with a proper one!
        commit_message: Set default README
```

Example 2 - unify GitLab CI pipeline config in the first branch found: develop or main:
```yaml
projects_and_groups:
  group_1/project_1:
    files:
      ".gitlab-ci.yml":
        overwrite: true
        branches:
          - develop
          - main
        only_first_branch: true
        content: |
          stages:
            - test

          test:
            image: node:6
            stage: test
            script:
              - npm test
```

Example 3 - templates:
```yaml
projects_and_groups:
  group_1/project_1:
    files:
      "file-using-templating":
        branches: all
        content: |
          Simple templating is supported via jinja2 with two default variables
          {{ project }} will be replaced by project name, while {{ group }} by a group name.
          All occurrences will be replaced.
      "file-escape-templating":
        branches: all
        template: no
        content: |
          {{ project }} will be rendered literally
      "file-with-custom-variable":
        branches: all
        content: |
          {{ foo }} and {{ bar }} are defined by you, but currently only dict is supported for jinja_env.
          Group: {{ group }} and project: {{ project }} are always accessable by jinja.
        jinja_env:
          foo: "fooz"
          bar: "barz"
```

Example 4 - deleting files:
```yaml
projects_and_groups:
  group_1/project_1:
    files:
      "some-path/garbage-file":
        delete: true
        branches:
          - develop
          - main
        only_first_branch: true
        skip_ci: true
```
