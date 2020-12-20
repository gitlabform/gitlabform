class SafeDict(dict):
    """
    A dict that a "get" method that allows to use a path-like reference to its subdict values.

    For example with a dict like {"key": {"subkey": {"subsubkey": "value"}}}
    you can use a string 'key|subkey|subsubkey' to get the 'value'.

    The default value is returned if ANY of the subelements does not exist.

    Code based on https://stackoverflow.com/a/44859638/2693875
    """

    def __init__(self, seq=None, key_path_separator: str = "|", exclude_keys=[]):
        super(SafeDict, self).__init__(seq)
        for excluded_key in exclude_keys:
            self.pop(excluded_key)
        self.key_path_separator = key_path_separator

    def get(self, path, default=None):
        keys = path.split(self.key_path_separator)
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
