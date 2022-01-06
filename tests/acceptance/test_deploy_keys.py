from tests.acceptance import (
    run_gitlabform,
)


def single_true(iterable):
    i = iter(iterable)
    # use the fact that thanks to iter() we will "consume"
    # all the elements of iterable up to the one that is True
    # so that there should be no other True in the rest
    return any(i) and not any(i)


class TestDeployKeys:
    def test__deploy_key_add(self, gitlab, group_and_project_for_function):

        # noinspection PyPep8
        key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDydRMMBVOXfD76kjfI9wjxcSkJqdqr9222naDd6EGLuoDPjwRdowGJXTPLO88iFux2hWpROfT3PaP8s/yi0LkKSi2Fwn4hEc9u8pVoXQVhEwu367cLmy0XCo5lOmkfXaBSvLqb+Z6v9CozdJzmsllcTCK1DoYcGD8NPnQMMEETqbHzropjUjLA/to/zfI/mYVP86X15w+pw0DsUtspj3MmQBxPks4v2EAF7tUGLgqMHMr/z5bsWkm6yR4fv7rfjLoh10tXUY8WrVvzAZzWCs7fnP1qf5CCU7MlzggSIhzbwLn2DcYMBnFKGgx3H/VwJIvtmoIq8duedlUQ8zxKaSK8ziF/WQ8EtMW19qCrI8W+6vOgJpooDpBkPnSE+gsS+ANyWoXOJhgGukjPtphYqGTvDQAAbAMIeXB7QqDwq62UkgRSr5TC4pTVQrzlRTLxrnWMpYhpYy/3fCvYWDvuRFV8+IH6mlXoCrcMfh78oShmwkv8+A9/j9pBBBiFBZ2x6sM="

        config_add = f"""
        projects_and_groups:
          {group_and_project_for_function}:
            deploy_keys:
              foobar:
                key: {key}
                title: some_key
        """
        run_gitlabform(config_add, group_and_project_for_function)

        deploy_keys = gitlab.get_deploy_keys(group_and_project_for_function)
        assert single_true([key["title"] == "some_key" for key in deploy_keys])

    def test__deploy_key_add_delete(self, gitlab, group_and_project_for_function):

        # noinspection PyPep8
        key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDydRMMBVOXfD76kjfI9wjxcSkJqdqr9222naDd6EGLuoDPjwRdowGJXTPLO88iFux2hWpROfT3PaP8s/yi0LkKSi2Fwn4hEc9u8pVoXQVhEwu367cLmy0XCo5lOmkfXaBSvLqb+Z6v9CozdJzmsllcTCK1DoYcGD8NPnQMMEETqbHzropjUjLA/to/zfI/mYVP86X15w+pw0DsUtspj3MmQBxPks4v2EAF7tUGLgqMHMr/z5bsWkm6yR4fv7rfjLoh10tXUY8WrVvzAZzWCs7fnP1qf5CCU7MlzggSIhzbwLn2DcYMBnFKGgx3H/VwJIvtmoIq8duedlUQ8zxKaSK8ziF/WQ8EtMW19qCrI8W+6vOgJpooDpBkPnSE+gsS+ANyWoXOJhgGukjPtphYqGTvDQAAbAMIeXB7QqDwq62UkgRSr5TC4pTVQrzlRTLxrnWMpYhpYy/3fCvYWDvuRFV8+IH6mlXoCrcMfh78oShmwkv8+A9/j9pBBBiFBZ2x6sM="

        config_add = f"""
        projects_and_groups:
          {group_and_project_for_function}:
            deploy_keys:
              foobar:
                key: {key}
                title: some_key
        """
        run_gitlabform(config_add, group_and_project_for_function)

        deploy_keys = gitlab.get_deploy_keys(group_and_project_for_function)
        assert single_true([key["title"] == "some_key" for key in deploy_keys])

        # noinspection PyPep8
        config_delete = f"""
        projects_and_groups:
          {group_and_project_for_function}:
            deploy_keys:
              foobar:
                title: some_key
                delete: true
        """
        run_gitlabform(config_delete, group_and_project_for_function)

        deploy_keys = gitlab.get_deploy_keys(group_and_project_for_function)
        assert not any([key["title"] == "some_key" for key in deploy_keys])

    def test__deploy_key_add_delete_readd(self, gitlab, group_and_project_for_function):

        # noinspection PyPep8
        key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDydRMMBVOXfD76kjfI9wjxcSkJqdqr9222naDd6EGLuoDPjwRdowGJXTPLO88iFux2hWpROfT3PaP8s/yi0LkKSi2Fwn4hEc9u8pVoXQVhEwu367cLmy0XCo5lOmkfXaBSvLqb+Z6v9CozdJzmsllcTCK1DoYcGD8NPnQMMEETqbHzropjUjLA/to/zfI/mYVP86X15w+pw0DsUtspj3MmQBxPks4v2EAF7tUGLgqMHMr/z5bsWkm6yR4fv7rfjLoh10tXUY8WrVvzAZzWCs7fnP1qf5CCU7MlzggSIhzbwLn2DcYMBnFKGgx3H/VwJIvtmoIq8duedlUQ8zxKaSK8ziF/WQ8EtMW19qCrI8W+6vOgJpooDpBkPnSE+gsS+ANyWoXOJhgGukjPtphYqGTvDQAAbAMIeXB7QqDwq62UkgRSr5TC4pTVQrzlRTLxrnWMpYhpYy/3fCvYWDvuRFV8+IH6mlXoCrcMfh78oShmwkv8+A9/j9pBBBiFBZ2x6sM="

        config_add = f"""
        projects_and_groups:
          {group_and_project_for_function}:
            deploy_keys:
              foobar:
                key: {key}
                title: some_key
        """
        run_gitlabform(config_add, group_and_project_for_function)

        deploy_keys = gitlab.get_deploy_keys(group_and_project_for_function)
        assert single_true([key["title"] == "some_key" for key in deploy_keys])

        # noinspection PyPep8
        config_delete = f"""
        projects_and_groups:
          {group_and_project_for_function}:
            deploy_keys:
              foobar:
                title: some_key
                delete: true
        """
        run_gitlabform(config_delete, group_and_project_for_function)

        deploy_keys = gitlab.get_deploy_keys(group_and_project_for_function)
        assert not any([key["title"] == "some_key" for key in deploy_keys])

        run_gitlabform(config_add, group_and_project_for_function)
        deploy_keys = gitlab.get_deploy_keys(group_and_project_for_function)
        assert single_true([key["title"] == "some_key" for key in deploy_keys])

    def test__deploy_key_add_delete_readd_under_different_name(
        self, gitlab, group_and_project_for_function
    ):

        # noinspection PyPep8
        key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDydRMMBVOXfD76kjfI9wjxcSkJqdqr9222naDd6EGLuoDPjwRdowGJXTPLO88iFux2hWpROfT3PaP8s/yi0LkKSi2Fwn4hEc9u8pVoXQVhEwu367cLmy0XCo5lOmkfXaBSvLqb+Z6v9CozdJzmsllcTCK1DoYcGD8NPnQMMEETqbHzropjUjLA/to/zfI/mYVP86X15w+pw0DsUtspj3MmQBxPks4v2EAF7tUGLgqMHMr/z5bsWkm6yR4fv7rfjLoh10tXUY8WrVvzAZzWCs7fnP1qf5CCU7MlzggSIhzbwLn2DcYMBnFKGgx3H/VwJIvtmoIq8duedlUQ8zxKaSK8ziF/WQ8EtMW19qCrI8W+6vOgJpooDpBkPnSE+gsS+ANyWoXOJhgGukjPtphYqGTvDQAAbAMIeXB7QqDwq62UkgRSr5TC4pTVQrzlRTLxrnWMpYhpYy/3fCvYWDvuRFV8+IH6mlXoCrcMfh78oShmwkv8+A9/j9pBBBiFBZ2x6sM="

        config_add = f"""
            projects_and_groups:
              {group_and_project_for_function}:
                deploy_keys:
                  foobar:
                    key: {key}
                    title: a_title
            """
        run_gitlabform(config_add, group_and_project_for_function)

        deploy_keys = gitlab.get_deploy_keys(group_and_project_for_function)
        assert single_true([key["title"] == "a_title" for key in deploy_keys])

        # noinspection PyPep8
        config_delete = f"""
            projects_and_groups:
              {group_and_project_for_function}:
                deploy_keys:
                  foobar:
                    title: a_title
                    delete: true
            """
        run_gitlabform(config_delete, group_and_project_for_function)

        deploy_keys = gitlab.get_deploy_keys(group_and_project_for_function)
        assert not any([key["title"] == "a_title" for key in deploy_keys])

        # noinspection PyPep8
        config_readd = f"""
            projects_and_groups:
              {group_and_project_for_function}:
                deploy_keys:
                  foobar:
                    key: {key}
                    title: another_title
            """
        run_gitlabform(config_readd, group_and_project_for_function)
        deploy_keys = gitlab.get_deploy_keys(group_and_project_for_function)
        assert single_true([key["title"] == "another_title" for key in deploy_keys])

    def test__deploy_key_update_title(self, gitlab, group_and_project_for_function):

        key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCz7QLHyLval1TS+MvLN9QwLi5It7f74BQWi7d5gxBKA7BaGxebOc3AmLF9B/XkBfSNLOEhKO6NZrq07U4C2c3j29IvHy1oAk/cg6YmDL6U7d9lxBxYHC/SsnN70LekGbjHhaMofNvfnDOpS7n5MvJjY42ovxag+SRAOhtp541no6R/Oj9OoW6Y3AtX59HIcP1JvGTx/Ohb8OUwOXbfIDxrqR4qt1kiSPLAAC8wLNNDTUYs89TVAqyvzuXXindmcXosVcEQ6EYzHPin66ge1rAYJfhBqei1tmS0OUrW4awzQxddBqrwVBq0occUrbkjJNRfEjHjYR2GDutk8bP/kZ7cJ3RMU7bCh6CNGvApN7BysSfFcS19/18BCVjWFWbZSHGoaB0DDjl9R5s7RzMuBvNULt4yTEQUOQKdmteJY6RxKApxiCglu8I+8fIzL75iDNejZ+UlXj1SnIfe2BrzR/EN2FAGubq2SLmKLGLSGk3lkwDBdPfNMjYJG9bdaeHt2mc="

        config = f"""
            projects_and_groups:
              {group_and_project_for_function}:
                deploy_keys:
                  foobar:
                    key: {key}
                    title: title_before
            """
        run_gitlabform(config, group_and_project_for_function)

        deploy_keys = gitlab.get_deploy_keys(group_and_project_for_function)
        assert single_true([key["title"] == "title_before" for key in deploy_keys])

        config = f"""
            projects_and_groups:
              {group_and_project_for_function}:
                deploy_keys:
                  # because it's the title that defines the key, we cannot immediately change key's title in the config.
                  # we need two element config - 1. delete it under old title, 2. add it under new title
                  foo:
                    title: title_before
                    delete: true
                  bar:
                    key: {key}
                    title: title_after
            """
        run_gitlabform(config, group_and_project_for_function)

        deploy_keys = gitlab.get_deploy_keys(group_and_project_for_function)
        assert single_true([key["title"] == "title_after" for key in deploy_keys])
        assert not any([key["title"] == "title_before" for key in deploy_keys])

    def test__deploy_key_update_value(self, gitlab, group_and_project_for_function):

        # noinspection PyPep8
        key_before = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCz7QLHyLval1TS+MvLN9QwLi5It7f74BQWi7d5gxBKA7BaGxebOc3AmLF9B/XkBfSNLOEhKO6NZrq07U4C2c3j29IvHy1oAk/cg6YmDL6U7d9lxBxYHC/SsnN70LekGbjHhaMofNvfnDOpS7n5MvJjY42ovxag+SRAOhtp541no6R/Oj9OoW6Y3AtX59HIcP1JvGTx/Ohb8OUwOXbfIDxrqR4qt1kiSPLAAC8wLNNDTUYs89TVAqyvzuXXindmcXosVcEQ6EYzHPin66ge1rAYJfhBqei1tmS0OUrW4awzQxddBqrwVBq0occUrbkjJNRfEjHjYR2GDutk8bP/kZ7cJ3RMU7bCh6CNGvApN7BysSfFcS19/18BCVjWFWbZSHGoaB0DDjl9R5s7RzMuBvNULt4yTEQUOQKdmteJY6RxKApxiCglu8I+8fIzL75iDNejZ+UlXj1SnIfe2BrzR/EN2FAGubq2SLmKLGLSGk3lkwDBdPfNMjYJG9bdaeHt2mc="
        key_after = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICRgWbMGu+88gPVPEIAHQdG958oTzSFmuBnwmC0hunyp"

        config = f"""
        projects_and_groups:
          {group_and_project_for_function}:
            deploy_keys:
              foobar:
                key: {key_before}
                title: a_key
        """
        run_gitlabform(config, group_and_project_for_function)

        deploy_keys = gitlab.get_deploy_keys(group_and_project_for_function)
        assert any([key["key"] == key_before for key in deploy_keys])

        config = f"""
        projects_and_groups:
          {group_and_project_for_function}:
            deploy_keys:
              foobar:
                key: {key_after}
                title: a_key
        """
        run_gitlabform(config, group_and_project_for_function)

        deploy_keys = gitlab.get_deploy_keys(group_and_project_for_function)
        assert not any([key["key"] == key_before for key in deploy_keys])
        assert any([key["key"] == key_after for key in deploy_keys])
