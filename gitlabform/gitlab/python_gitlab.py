import functools

from gitlab import Gitlab, GitlabGetError
from gitlab.base import RESTObject, RESTObjectList
from gitlab.v4.objects import Group


# Extends the python-gitlab class to add convenience wrappers for common functionality used within gitlabform
class PythonGitlab(Gitlab):
    def get_user_id(self, username) -> int:
        user = self.get_user_by_username(username)
        return user.id

    def get_group_id(self, groupname) -> int:
        groups = self.get_group_by_groupname(groupname)
        return groups.id

    def get_group_by_name(self, groupname: str) -> Group:
        group = self.get_group_by_groupname(groupname)
        return self.groups.get(group.id)

        #  Uses "LIST" to get a group by groupname, to get the full Group object, call get using the group's id

    @functools.lru_cache()
    def get_group_by_groupname(self, groupname: str) -> RESTObject:
        groups = self.groups.list(search=groupname)
        if len(groups) == 0:
            raise GitlabGetError(
                "No groups found when searching for groupname '%s'" % groupname, 404
            )

        # Highly unlikely to ever execute as Gitlab will only return paginated list if we get lots of results
        # given search is by groupname, we should not expect > 1
        if isinstance(groups, RESTObjectList):
            raise GitlabGetError(
                "Too many groups found using groupname '%s' please specify more accurately in config"
                % groupname,
                404,
            )

        return groups[0]

    #  Uses "LIST" to get a user by username, to get the full User object, call get using the user's id
    @functools.lru_cache()
    def get_user_by_username(self, username: str) -> RESTObject:
        users = self.users.list(username=username)
        if len(users) == 0:
            raise GitlabGetError(
                "No users found when searching for username '%s'" % username, 404
            )

        # Highly unlikely to ever execute as Gitlab will only return paginated list if we get lots of results
        # given search is by username, we should not expect > 1
        if isinstance(users, RESTObjectList):
            raise GitlabGetError(
                "Too many users found using username '%s' please specify more accurately in config"
                % username,
                404,
            )

        return users[0]
