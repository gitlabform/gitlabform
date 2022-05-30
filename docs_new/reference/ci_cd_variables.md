# CI/CD variables

Please note that project-level and group-level [CI/CD variables](https://docs.gitlab.com/ee/ci/variables/) (used to be known as "Secret Variables") are different entities in GitLab!

## Project CI/CD variables

This section purpose is to manage the **project-level** CI/CD variables.

The keys and values for each variable should be as documented in the [Project-Level Variables API docs](https://docs.gitlab.com/ee/api/project_level_variables.html#create-variable), **except the id**.

You can make the:

* [protected variables](https://docs.gitlab.com/ee/ci/variables/#protected-cicd-variables)
* [masked variables](https://docs.gitlab.com/ee/ci/variables/#mask-a-cicd-variable)
* [variables limited to the scope of specific environment(s)](https://docs.gitlab.com/ee/ci/variables/#limit-the-environment-scope-of-a-cicd-variable)

!!! info

    Variables limited to the scope of specific environment(s) requires GitLab Premium (paid). (This is a GitLab's limitation, not GitLabForm's.)

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    secret_variables:
      # --- Adding/resetting
      a_friendly_secret_variable_name: # this is just a label
        key: SSH_PRIVATE_KEY_BASE64
        value: "LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUl (...)"

      # --- Adding/resetting protected variable
      my_protected_variable:
        key: PROTECTED_VAR
        value: "foobar-123-123-123"
        protected: true

      # --- Adding/resetting masked variable
      my_masked_variable:
        key: MASKED_VAR
        value: "foobar-123-123-123"
        masked: true

      # --- Adding/resetting variables per environment
      aws_access_key_id_for_deploying_in_production:
        key: APP_HOST_AWS_ACCESS_KEY_ID
        value: "prod-value-1234"
        protected: true
        masked: true
        environment_scope: production
        filter[environment_scope]: production
      aws_access_key_id_for_deploying_in_staging:
        key: APP_HOST_AWS_ACCESS_KEY_ID
        value: "staging-value-1234"
        protected: true
        masked: true
        environment_scope: staging
        filter[environment_scope]: staging

      # --- Deleting
      # the below name is not used by GitLab, it's just for you
      a_secret_you_want_to_remove:
        key: MY_SECRET
        delete: true
```

## Group CI/CD variables

This section purpose is to manage the **group-level** CI/CD variables.

The keys and values for each variable should be as documented in the [Group-Level Variables API docs](https://docs.gitlab.com/ee/api/group_level_variables.html#create-variable), **except the id**.

Although we do not provide examples like for the project-level variables, all the features like above are also supported:

* protected variables,
* masked variables,
* variables limited to the scope of specific environment(s).

!!! info

    Variables limited to the scope of specific environment(s) requires GitLab Premium (paid). (This is a GitLab's limitation, not GitLabForm's.)

Example:
```yaml
projects_and_groups:
  group_1/*:
    group_secret_variables:
      # --- Adding/resetting
      a_secret_you_want_to_add_to_all_groups_in_your_gitlab_instance: # this is just a label
        key: A_NEW_PASSWORD
        value: "ThisIsAVerySecretPassword"
        variable_type: env_var # or file
        protected: false

      # --- Deleting
      old_variable:
        key: PASSWORD
        delete: true
```
