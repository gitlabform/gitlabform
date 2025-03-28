from gitlabform.gitlab.groups import GitLabGroups
import os
import logging


class GitLabGroupAvatar(GitLabGroups):
    def update_group_avatar(self, group_name, avatar_path=None):
        """
        Update the avatar of a GitLab group using an image file

        Args:
            group_name: The group identifier (group or subgroup path)
            avatar_path: Path to the image file, relative to the current working directory
        """

        # Get the full path to the image
        full_path = os.path.abspath(avatar_path)

        # Check if the file exists
        if not os.path.exists(full_path):
            logging.error(f"Avatar file not found: {full_path}")
            return

        # We need to use multipart/form-data to upload the image
        # This requires using the underlying session directly rather than the _make_requests_to_api method
        group_id = self._get_group_id(group_name)
        url = f"{self.url}/api/v4/groups/{group_id}"

        # Open the file for sending
        with open(full_path, "rb") as avatar_file:
            # Prepare the file data
            files = {"avatar": (os.path.basename(avatar_path), avatar_file)}

            # Send the request
            return self.session.put(url, files=files, timeout=self.timeout)

    def delete_group_avatar(self, group_name):
        """
        Remove the avatar of a GitLab group

        Args:
            group_name: The group identifier (group or subgroup path)
        """

        group_id = self._get_group_id(group_name)
        url = f"{self.url}/api/v4/groups/{group_id}"

        # Put without avatar file
        return self.session.put(url, data={"avatar": ""}, timeout=self.timeout)
