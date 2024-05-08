from logging import debug, info
from typing import Dict, List

from gitlabform.gitlab import GitLab
from gitlabform.processors.abstract_processor import AbstractProcessor

from gitlab.v4.objects import Group


class GroupLabelsProcessor(AbstractProcessor):
    def __init__(self, gitlab: GitLab):
        super().__init__("group_labels", gitlab)

    def _process_configuration(self, group_path_and_name: str, configuration: Dict):
        configured_labels = configuration.get("group_labels", {})

        enforce_labels = configuration.get("group_labels|enforce", False)

        # Remove 'enforce' key from the config so that it's not treated as a "label"
        if enforce_labels:
            configured_labels.pop("enforce")

        group: Group = self.gl.get_group_by_path_cached(group_path_and_name)

        existing_labels = group.labels.list()
        existing_label_names = []

        if existing_labels:
            for label_name in existing_labels:
                full_label = group.labels.get(label_name.id)
                label_name = full_label.name

                if label_name not in configured_labels.keys():
                    debug(f"{label_name} not in configured labels")
                    # only delete labels when enforce is true, because user's maybe automatically applying labels based
                    # on Repo state, for example: Compliance Framework labels based on language or CI-template status
                    if enforce_labels:
                        info(f"Removing {label_name} from group")
                        full_label.delete()
                else:
                    info(f"Updating {label_name} on group")
                    configured_label = configured_labels.get(label_name)
                    existing_label_names.append(label_name)
                    if self._needs_update(full_label.asdict(), configured_label):
                        # label api in python-gitlab does not supply an update() method
                        for key in configured_label:
                            full_label.__setattr__(key, configured_label[key])

                        full_label.save()

        # add new labels
        for label_name in configured_labels.keys():
            if label_name not in existing_label_names:
                label = configured_labels.get(label_name)
                info(f"Adding {label_name} to group")
                group.labels.create({"name": label_name, **label})
