# CI/CD variables

Please note that project-level and group-level CI/CD variables (used to known as "Secret Variables") are different entities in GitLab!

## Project CI/CD variables

This section purpose is to manage the **project-level** CI/CD variables.

Example:

```yaml
projects_and_groups:
  group_1/project_1:
    secret_variables:
      # --- Adding/resetting
      # the below name is not used by GitLab, it's just for you
      a_friendly_secret_variable_name:
        # keys and values below are as described at https://docs.gitlab.com/ee/api/project_level_variables.html#create-variable, except the id
        key: SSH_PRIVATE_KEY_BASE64
        value: "LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUl (...)"

      # --- Adding/resetting masked variable
      # the below name is not used by GitLab, it's just for you
      my_masked_variable:
        # keys and values below are as described at https://docs.gitlab.com/ee/api/project_level_variables.html#create-variable, except the id
        key: SSH_PRIVATE_KEY_BASE64
        value: "foobar-123-123-123"
        # note that there are extra requirements for variables to be "masked",
        # see https://docs.gitlab.com/ee/ci/variables/#mask-a-cicd-variable
        # for more information
        masked: true

      # --- Adding/resetting variables per environment 
      # Variables can be scoped to an "environment".
      # Scoping to environment also allows using the same "key" name for multiple variables.
      # This can simplify CI Config file because the appropriate variable will be exposed
      # by GitLab to the job that is targetting a given environment. If the same "key" name
      # is used for different environments, you'll need to add filter[environment_scope] to
      # configuration as shown below.
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

Example:
```yaml
projects_and_groups:
  group_1/*:
    group_secret_variables:
      # --- Adding/resetting
      # the below name is not used by GitLab, it's just for you
      a_secret_you_want_to_add_to_all_groups_in_your_gitlab_instance:
        # keys and values below are as described at https://docs.gitlab.com/ee/api/group_level_variables.html#create-variable
        key: A_NEW_PASSWORD
        value: "ThisIsAVerySecretPassword"
        variable_type: env_var # or file
        protected: false

      # --- Deleting
      # the below name is not used by GitLab, it's just for you
      old_variable:
        key: PASSWORD
        delete: true
```
