from cli_ui import debug as verbose, info, warning
from typing import Dict, List, Callable, Union

from gitlab.base import RESTObjectList, RESTObject
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
        existing_group_labels = group_or_project.labels.list(get_all=True, include_ancestor_groups=False)
        existing_group_and_parent_labels = group_or_project.labels.list(get_all=True)
        existing_label_keys: List = []

        if isinstance(group_or_project, Group):
            parent_object_type = "Group"
        else:
            parent_object_type = "Project"

        gitlab_labels_to_delete: List = []

        for label_to_update in existing_group_labels:
            label_name_in_gl = label_to_update.name
            updated_label = False
            verbose(f"Checking if {label_name_in_gl} is in Configuration to update or delete")

            for key, configured_label in configured_labels.items():
                configured_label_name = configured_label.get("name")
                # Key in YAML may not match the "name" value in Gitlab or YAML, so we must match on both
                if self.configured_label_matches_gitlab_label(configured_label_name, key, label_name_in_gl):
                    # label exists in GL, so update
                    existing_label_keys.append(key)
                    updated_label = True

                    if needs_update(label_to_update.asdict(), configured_label):
                        self.update_existing_label(
                            configured_label,
                            self.get_label(group_or_project, label_to_update),
                            parent_object_type,
                        )
                    else:
                        verbose(f"No update required for label: {label_name_in_gl}")
                    break

            if not updated_label:
                gitlab_labels_to_delete.append(label_to_update)

        # Delete labels no longer in config
        for label_to_delete in gitlab_labels_to_delete:
            label_name_in_gl = label_to_delete.name

            verbose(f"{label_name_in_gl} not in configured labels")
            # only delete labels when enforce is true, because user's maybe automatically applying labels based
            # on Repo state, for example: Compliance Framework labels based on language or CI-template status
            if enforce:
                info(f"Removing {label_name_in_gl} from {parent_object_type}")
                self.get_label(group_or_project, label_to_delete).delete()

        # add new labels

        for label_key in configured_labels.keys():
            if label_key not in existing_label_keys:
                info(f"Creating new label with key: {label_key}, on {parent_object_type}")
                self.create_new_label(
                    configured_labels, group_or_project, label_key, parent_object_type, existing_group_and_parent_labels
                )

    @staticmethod
    def configured_label_matches_gitlab_label(configured_label_name: str, key: str, label_name_in_gl: str):
        return (
            configured_label_name is not None and label_name_in_gl == configured_label_name
        ) or label_name_in_gl == key

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

    def create_new_label(
        self,
        configured_labels,
        group_or_project: Group | Project,
        label_key: str,
        parent_object_type: str,
        existing_group_and_parent_labels: Union[List[GroupLabel], List[ProjectLabel]],
    ):
        label = configured_labels.get(label_key)
        configured_label_name = label.get("name")
        found_existing_label = False
        for existing_label in existing_group_and_parent_labels:
            if self.configured_label_matches_gitlab_label(configured_label_name, label_key, existing_label.name):
                warning(
                    f"Label {existing_label.name} already exists either in {group_or_project.name} or on Parent Group, so will not create"
                )
                found_existing_label = True
                break

        if not found_existing_label:
            info(f"Adding label with key: {label_key} to {parent_object_type}")
            group_or_project.labels.create({"name": label_key, **label})
