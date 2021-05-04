from functools import wraps


class SafeDict(dict):
    """
    A dict that a "get" method that allows to use a path-like reference to its subdict values.

    For example with a dict like {"key": {"subkey": {"subsubkey": "value"}}}
    you can use a string 'key|subkey|subsubkey' to get the 'value'.

    The default value is returned if ANY of the subelements does not exist.

    Code based on https://stackoverflow.com/a/44859638/2693875
    """

    def get(self, path, default=None):
        keys = path.split("|")
        val = None

        for key in keys:
            if val:
                if isinstance(val, list):
                    val = [v.get(key, default) if v else None for v in val]
                else:
                    val = val.get(key, default)
            else:
                val = dict.get(self, key, default)

            if not val:
                break

        return val


def configuration_to_safe_dict(method):
    """
    This wrapper function calls the method with the configuration converted from a regular dict into a SafeDict
    """

    @wraps(method)
    def method_wrapper(self, project_and_group, configuration, *args):
        return method(self, project_and_group, SafeDict(configuration), *args)

    return method_wrapper
