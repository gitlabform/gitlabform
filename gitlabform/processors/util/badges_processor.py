import sys
from logging import critical, info
from typing import Callable, Dict, List, Union

from gitlab.v4.objects import Group, GroupBadge, Project, ProjectBadge

from gitlabform.constants import EXIT_INVALID_INPUT


class BadgesProcessor:
    """
    Shared badge sync logic for project and group badges.

    Groups and Projects share the same .badges manager API within python-gitlab
    (both use CRUDMixin), so a single helper can drive both.
    """

    def process_badges(
        self,
        configuration_name: str,
        configured_badges: Dict,
        enforce: bool,
        group_or_project: Union[Group, Project],
        needs_update: Callable,
    ) -> None:
        display_name = getattr(group_or_project, "path_with_namespace", None) or group_or_project.full_path

        self._find_duplicates(configuration_name, display_name, configured_badges)

        existing_badges = self._list_existing_badges(group_or_project)

        handled_names: set = set()

        for entity_name, badge_config in configured_badges.items():
            name = badge_config.get("name")
            if not name:
                critical(
                    f"Entity {entity_name} in {configuration_name} for {display_name}"
                    f" doesn't have its defining key: 'name'"
                )
                sys.exit(EXIT_INVALID_INPUT)

            matching = next((b for b in existing_badges if b.name == name), None)

            if badge_config.get("delete", False):
                if matching:
                    info(f"Deleting {entity_name} of {configuration_name} in {display_name}")
                    matching.delete()
                handled_names.add(name)
                continue

            self._validate_required(configuration_name, display_name, entity_name, badge_config)

            if matching:
                if needs_update(matching.asdict(), badge_config):
                    info(f"Editing {entity_name} of {configuration_name} in {display_name}")
                    for key, value in badge_config.items():
                        setattr(matching, key, value)
                    matching.save()
                else:
                    info(f" * {entity_name} of {configuration_name} in {display_name} doesn't need an update.")
            else:
                info(f" * Adding {entity_name} of {configuration_name} in {display_name}")
                group_or_project.badges.create(badge_config)
            handled_names.add(name)

        if enforce:
            for existing in existing_badges:
                if existing.name not in handled_names:
                    info(
                        f"Deleting badge '{existing.name}' of {configuration_name} in {display_name}"
                        f" as it's not in config and enforce is set to true."
                    )
                    existing.delete()

    @staticmethod
    def _list_existing_badges(
        group_or_project: Union[Group, Project],
    ) -> List[Union[GroupBadge, ProjectBadge]]:
        badges = group_or_project.badges.list(get_all=True)
        # For projects, .badges.list() also returns badges inherited from the parent group,
        # so we must filter to project-kind only. The group endpoint returns only group badges.
        if isinstance(group_or_project, Project):
            return [b for b in badges if b.kind == "project"]
        return list(badges)

    @staticmethod
    def _find_duplicates(configuration_name: str, display_name: str, configured_badges: Dict) -> None:
        seen: Dict[str, str] = {}
        for key, badge in configured_badges.items():
            name = badge.get("name")
            if name is None:
                continue
            if name in seen:
                critical(
                    f"Entities {seen[name]} and {key} in {configuration_name} for {display_name}"
                    f" are the same in terms of their defining key: 'name'"
                )
                sys.exit(EXIT_INVALID_INPUT)
            seen[name] = key

    @staticmethod
    def _validate_required(configuration_name: str, display_name: str, entity_name: str, badge_config: Dict) -> None:
        missing = [key for key in ("name", "link_url", "image_url") if not badge_config.get(key)]
        if missing:
            critical(
                f"Entity {entity_name} in {configuration_name} for {display_name}"
                f" doesn't have some of its keys required to create or update:"
                f" {', '.join(missing)}"
            )
            sys.exit(EXIT_INVALID_INPUT)
