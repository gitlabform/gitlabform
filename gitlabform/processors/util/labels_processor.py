from cli_ui import debug as verbose, info
from typing import Dict, List, Callable

from gitlab.v4.objects import Group, Project, ProjectLabel, GroupLabel


class LabelsProcessor:

    # Groups and Projects share the same API for .labels within python-gitlab
    def process_labels(
        self,
        configured_labels: Dict,
        enforce: bool,
        group_or_project: Group | Project,
        needs_update: Callable,  # self._needs_update passed from AbstractProcessor called process_labels
    ):
        # Only get Labels created directly on the project/group
        existing_labels = group_or_project.labels.list(get_all=True, include_ancestor_groups=False)
        existing_label_names: List = []

        if isinstance(group_or_project, Group):
            parent_object_type = "Group"
        else:
            parent_object_type = "Project"

        if existing_labels:
            for listed_label in existing_labels:
                # list and get single label return the same data from Gitlab so we can save on API calls
                # by only GETting again when we need to make an update or delete
                # https://docs.gitlab.com/api/labels/ && https://docs.gitlab.com/api/group_labels/
                verbose(f"Processing existing label in Gitlab: {listed_label.name}")
                label_name = listed_label.name

                if label_name not in configured_labels.keys():
                    verbose(f"{label_name} not in configured labels")
                    # only delete labels when enforce is true, because user's maybe automatically applying labels based
                    # on Repo state, for example: Compliance Framework labels based on language or CI-template status
                    if enforce:
                        info(f"Removing {label_name} from {parent_object_type}")
                        self.get_label(group_or_project, listed_label).delete()
                else:
                    configured_label = configured_labels.get(label_name)
                    existing_label_names.append(label_name)

                    if needs_update(listed_label.asdict(), configured_label):
                        self.update_existing_label(
                            configured_label,
                            self.get_label(group_or_project, listed_label),
                            parent_object_type,
                        )
                    else:
                        verbose(f"No update required for label: {label_name}")

        # add new labels
        for label_name in configured_labels.keys():
            if label_name not in existing_label_names:
                info(f"Creating new label: {label_name}, on {parent_object_type}")
                self.create_new_label(configured_labels, group_or_project, label_name, parent_object_type)

    @staticmethod
    def get_label(group_or_project, listed_label) -> GroupLabel | ProjectLabel:
        return group_or_project.labels.get(listed_label.id)

    @staticmethod
    def update_existing_label(
        configured_label,
        full_label: GroupLabel | ProjectLabel,
        parent_object_type: str,
    ):
        info(f"Updating {full_label.name} on {parent_object_type}")

        # label APIs in python-gitlab do not supply an update() method
        for key in configured_label:
            full_label.__setattr__(key, configured_label[key])

        full_label.save()

    @staticmethod
    def create_new_label(
        configured_labels,
        group_or_project: Group | Project,
        label_name: str,
        parent_object_type: str,
    ):
        label = configured_labels.get(label_name)
        info(f"Adding {label_name} to {parent_object_type}")
        group_or_project.labels.create({"name": label_name, **label})
