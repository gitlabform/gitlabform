from logging import debug, info
from typing import Dict, List, Callable

from gitlab.base import RESTObject
from gitlab.v4.objects import Group


class LabelsProcessor:

    # Groups and Projects share the same API for .labels within python-gitlab
    def process_labels(
        self,
        configured_labels: Dict,
        enforce: bool,
        group_or_project: RESTObject,  # Group | Project -> |: operand not supported in 3.8/3.9
        needs_update_method: Callable,
    ):
        existing_labels = group_or_project.labels.list()
        existing_label_names: List = []

        if isinstance(group_or_project, Group):
            parent_object_type = "Group"
        else:
            parent_object_type = "Project"

        if existing_labels:
            for listed_label in existing_labels:
                full_label = group_or_project.labels.get(listed_label.id)
                label_name = full_label.name

                if label_name not in configured_labels.keys():
                    self.process_label_not_in_config(
                        enforce, full_label, label_name, parent_object_type
                    )
                else:
                    self.update_existing_label(
                        configured_labels,
                        existing_label_names,
                        full_label,
                        label_name,
                        needs_update_method,
                        parent_object_type,
                    )

        # add new labels
        for label_name in configured_labels.keys():
            if label_name not in existing_label_names:
                self.create_new_label(
                    configured_labels, group_or_project, label_name, parent_object_type
                )

    def process_label_not_in_config(
        self,
        enforce: bool,
        full_label: RESTObject,  # GroupLabel | ProjectLabel
        label_name: str,
        parent_object_type: str,
    ):
        debug(f"{label_name} not in configured labels")
        # only delete labels when enforce is true, because user's maybe automatically applying labels based
        # on Repo state, for example: Compliance Framework labels based on language or CI-template status
        if enforce:
            info(f"Removing {label_name} from {parent_object_type}")
            full_label.delete()

    def update_existing_label(
        self,
        configured_labels,
        existing_label_names: List,
        full_label: RESTObject,  # GroupLabel | ProjectLabel
        label_name: str,
        needs_update_method: Callable,
        parent_object_type: str,
    ):
        info(f"Updating {label_name} on {parent_object_type}")
        configured_label = configured_labels.get(label_name)
        existing_label_names.append(label_name)

        if needs_update_method(full_label.asdict(), configured_label):
            # label APIs in python-gitlab do not supply an update() method
            for key in configured_label:
                full_label.__setattr__(key, configured_label[key])

            full_label.save()

    def create_new_label(
        self,
        configured_labels,
        group_or_project: RESTObject,  # Group | Project
        label_name: str,
        parent_object_type: str,
    ):
        label = configured_labels.get(label_name)
        info(f"Adding {label_name} to {parent_object_type}")
        group_or_project.labels.create({"name": label_name, **label})
