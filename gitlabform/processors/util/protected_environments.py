from logging import info
from typing import Any, Callable, Dict, Sequence, Tuple

ExistingProtectedEnvironment = Tuple[str, Dict[str, Any], Callable[[], Any]]


def sync_protected_environments(
    configuration_name: str,
    entity_path: str,
    configured_envs: Dict[str, Any],
    existing_envs: Sequence[ExistingProtectedEnvironment],
    create_env: Callable[[Dict[str, Any]], Any],
    needs_update: Callable[[Dict[str, Any], Dict[str, Any]], bool],
) -> None:
    # copy, so that popping "enforce" does not mutate the shared configuration,
    # which is reused when this method is retried
    envs_to_process: Dict[str, Any] = dict(configured_envs)
    enforce = envs_to_process.pop("enforce", False)

    processed_names: set[str] = set()

    for entity_name, env_config in envs_to_process.items():
        name = env_config.get("name", entity_name)
        matching = next((env for env in existing_envs if env[0] == name), None)

        if env_config.get("delete", False):
            if matching:
                info(f"Deleting {entity_name} of {configuration_name} in {entity_path}")
                matching[2]()
            else:
                info(
                    f"Not deleting {entity_name} of {configuration_name} in {entity_path}," f" because it doesn't exist"
                )
            processed_names.add(name)
            continue

        # "delete" is a gitlabform control key, not an environment attribute: it must not
        # trigger an update on every run, nor be sent to the API
        env_payload = {k: v for k, v in env_config.items() if k != "delete"}
        if "name" not in env_payload:
            env_payload["name"] = name

        if matching:
            if needs_update(matching[1], env_payload):
                # Recreate because GitLab's update endpoint requires record IDs and _destroy
                # flags to replace access levels, and python-gitlab lacks an update method.
                info(f" * Recreating {entity_name} of {configuration_name} in {entity_path}")
                matching[2]()
                create_env(env_payload)
            else:
                info(f" * {entity_name} of {configuration_name} in {entity_path}" f" doesn't need an update.")
        else:
            info(f" * Adding {entity_name} of {configuration_name} in {entity_path}")
            create_env(env_payload)
        processed_names.add(name)

    if enforce:
        for existing_name, _, delete_existing in existing_envs:
            if existing_name not in processed_names:
                info(
                    f"Deleting protected environment '{existing_name}' of {configuration_name}"
                    f" in {entity_path} as it's not in config and enforce is set to true."
                )
                delete_existing()
