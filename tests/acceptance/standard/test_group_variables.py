from tests.acceptance import run_gitlabform


class TestGroupVariables:
    def test__single_variable(self, group_for_function):
        config_single_variable = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_variable, group_for_function)

        variables = group_for_function.variables.list()
        assert len(variables) == 1

    def test__delete_variable(self, group_for_function):
        config_single_variable = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_variable, group_for_function)

        variables = group_for_function.variables.list()
        assert len(variables) == 1
        assert variables[0].value == "123"

        config_delete_variable = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo:
                key: FOO
                value: 123
                delete: true
        """

        run_gitlabform(config_delete_variable, group_for_function)

        variables = group_for_function.variables.list()
        assert len(variables) == 0

    def test__reset_single_variable(self, group_for_function):
        config_single_variable = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_variable, group_for_function)

        variables = group_for_function.variables.list()
        assert len(variables) == 1
        assert variables[0].value == "123"

        config_single_variable2 = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo:
                key: FOO
                value: 123456
        """

        run_gitlabform(config_single_variable2, group_for_function)

        variables = group_for_function.variables.list()
        assert len(variables) == 1
        assert variables[0].value == "123456"

    def test__more_variables(self, group_for_function):
        config_more_variables = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo:
                key: FOO
                value: 123456
              bar:
                key: BAR
                value: bleble
        """

        run_gitlabform(config_more_variables, group_for_function)

        variables = group_for_function.variables.list()
        variables_keys = {variable.key for variable in variables}
        assert len(variables) == 2
        assert variables_keys == {"FOO", "BAR"}

    def test__masked_variables(self, group_for_function):
        masked_variables = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo:
                key: FOO
                # https://docs.gitlab.com/ee/ci/variables/#masked-variable-requirements
                value: 12345678
                masked: true
        """

        run_gitlabform(masked_variables, group_for_function)

        variable = group_for_function.variables.get("FOO")
        assert variable.value == "12345678"
        assert variable.masked

    def test__protected_variables(self, group_for_function):
        protected_variables = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo:
                key: FOO
                value: 123
                protected: true
        """

        run_gitlabform(protected_variables, group_for_function)

        variable = group_for_function.variables.get("FOO")
        assert variable.value == "123"
        assert variable.protected

    def test__protected_change_variables(self, group_for_function):
        config_single_variable = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo:
                key: FOO
                value: 123
        """

        run_gitlabform(config_single_variable, group_for_function)

        variable = group_for_function.variables.get("FOO")
        assert variable.value == "123"
        assert variable.protected is False

        protected_variables = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo:
                key: FOO
                value: 123
                protected: true
        """

        run_gitlabform(protected_variables, group_for_function)

        variable = group_for_function.variables.get("FOO")
        assert variable.value == "123"
        assert variable.protected is True

    def test__not_masked_and_not_protected_variable(self, group_for_function):
        config_single_variable = f"""
        projects_and_groups:
          {group_for_function.full_path}/*:
            group_variables:
              foo:
                key: DOUBLE_NOT
                value: 123
                masked: false
                protected: false
        """

        run_gitlabform(config_single_variable, group_for_function)

        variable = group_for_function.variables.get("DOUBLE_NOT")
        assert variable.masked is False
        assert variable.protected is False
