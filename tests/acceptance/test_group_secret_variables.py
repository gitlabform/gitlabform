from tests.acceptance import run_gitlabform


class TestGroupSecretVariables:
    def test__single_secret_variable(self, gitlab, group_for_function):
        config_single_secret_variable = f"""
        projects_and_groups:
          {group_for_function}/*:
            group_secret_variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_secret_variable, group_for_function)

        secret_variables = gitlab.get_group_secret_variables(group_for_function)
        assert len(secret_variables) == 1

    def test__delete_secret_variable(self, gitlab, group_for_function):
        config_single_secret_variable = f"""
        projects_and_groups:
          {group_for_function}/*:
            group_secret_variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_secret_variable, group_for_function)

        secret_variables = gitlab.get_group_secret_variables(group_for_function)
        assert len(secret_variables) == 1
        assert secret_variables[0]["value"] == "123"

        config_delete_secret_variable = f"""
        projects_and_groups:
          {group_for_function}/*:
            group_secret_variables:
              foo:
                key: FOO
                value: 123
                delete: true
        """

        run_gitlabform(config_delete_secret_variable, group_for_function)

        secret_variables = gitlab.get_group_secret_variables(group_for_function)
        assert len(secret_variables) == 0

    def test__reset_single_secret_variable(self, gitlab, group_for_function):
        config_single_secret_variable = f"""
        projects_and_groups:
          {group_for_function}/*:
            group_secret_variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_secret_variable, group_for_function)

        secret_variables = gitlab.get_group_secret_variables(group_for_function)
        assert len(secret_variables) == 1
        assert secret_variables[0]["value"] == "123"

        config_single_secret_variable2 = f"""
        projects_and_groups:
          {group_for_function}/*:
            group_secret_variables:
              foo:
                key: FOO
                value: 123456
        """

        run_gitlabform(config_single_secret_variable2, group_for_function)

        secret_variables = gitlab.get_group_secret_variables(group_for_function)
        assert len(secret_variables) == 1
        assert secret_variables[0]["value"] == "123456"

    def test__more_secret_variables(self, gitlab, group_for_function):
        config_more_secret_variables = f"""
        projects_and_groups:
          {group_for_function}/*:
            group_secret_variables:
              foo:
                key: FOO
                value: 123456
              bar:
                key: BAR
                value: bleble
        """

        run_gitlabform(config_more_secret_variables, group_for_function)

        secret_variables = gitlab.get_group_secret_variables(group_for_function)
        secret_variables_keys = set([secret["key"] for secret in secret_variables])
        assert len(secret_variables) == 2
        assert secret_variables_keys == {"FOO", "BAR"}

    def test__masked_secret_variables(self, gitlab, group_for_function):
        masked_secret_variables = f"""
        projects_and_groups:
          {group_for_function}/*:
            group_secret_variables:
              foo:
                key: FOO
                # https://docs.gitlab.com/ee/ci/variables/#masked-variable-requirements
                value: 12345678
                masked: true
        """

        run_gitlabform(masked_secret_variables, group_for_function)

        secret_variable = gitlab.get_group_secret_variable_object(
            group_for_function, "FOO"
        )
        assert secret_variable["value"] == "12345678"
        assert secret_variable["masked"]

    def test__protected_secret_variables(self, gitlab, group_for_function):
        protected_secret_variables = f"""
        projects_and_groups:
          {group_for_function}/*:
            group_secret_variables:
              foo:
                key: FOO
                value: 123
                protected: true
        """

        run_gitlabform(protected_secret_variables, group_for_function)

        secret_variable = gitlab.get_group_secret_variable_object(
            group_for_function, "FOO"
        )
        assert secret_variable["value"] == "123"
        assert secret_variable["protected"]

    def test__protected_change_secret_variables(self, gitlab, group_for_function):
        config_single_secret_variable = f"""
        projects_and_groups:
          {group_for_function}/*:
            group_secret_variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_secret_variable, group_for_function)

        secret_variable = gitlab.get_group_secret_variable_object(
            group_for_function, "FOO"
        )
        assert secret_variable["value"] == "123"
        assert secret_variable["protected"] is False

        protected_secret_variables = f"""
        projects_and_groups:
          {group_for_function}/*:
            group_secret_variables:
              foo:
                key: FOO
                value: 123
                protected: true
        """

        run_gitlabform(protected_secret_variables, group_for_function)

        secret_variable = gitlab.get_group_secret_variable_object(
            group_for_function, "FOO"
        )
        assert secret_variable["value"] == "123"
        assert secret_variable["protected"] is True
