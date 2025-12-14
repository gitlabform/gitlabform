"""
Typed parser for GitLabForm configuration v5.

This parser creates specific configuration objects for each section
(badges, project_settings, push_rules, etc.) instead of generic nodes.
"""

from typing import Any, Dict, List, Optional
import ruamel.yaml

from gitlabform.configuration.yaml_tags import (
    GitLabFormTagOrderedDict,
    GitLabFormTagScalar,
    GitLabFormTagList,
    register_custom_tags,
)
# Control keys to skip when parsing badges
CONTROL_KEYS = ['enforce', 'inherit', 'keep_existing']

from gitlabform.configuration.config_v5_objects import (
    EntityConfig,
    BadgesConfig,
    BadgeConfig,
    ProjectSettingsConfig,
    GroupSettingsConfig,
    MembersConfig,
    MemberConfig,
    DeployKeysConfig,
    DeployKeyConfig,
    VariablesConfig,
    VariableConfig,
    LabelsConfig,
    LabelConfig,
    WebhooksConfig,
    WebhookConfig,
    ProtectedBranchesConfig,
    ProtectedBranchConfig,
    PushRulesConfig,
    AccessLevel,
    Visibility,
)


class ConfigV5TypedParser:
    """
    Parser for GitLabForm configuration v5 that creates typed configuration objects.
    
    This parser only supports YAML tags (!inherit, !enforce, etc.),
    not special key prefixes (_inherit, _enforce, etc.).
    """
    
    def __init__(self):
        """Initialize the parser."""
        self.yaml = ruamel.yaml.YAML()
        register_custom_tags(self.yaml)
    
    def parse(self, config_string: str) -> Dict[str, EntityConfig]:
        """
        Parse a configuration string into EntityConfig objects.
        
        Args:
            config_string: YAML configuration as string
            
        Returns:
            Dictionary mapping entity paths to EntityConfig objects
        """
        raw_config = self.yaml.load(config_string)
        
        if 'projects_and_groups' not in raw_config:
            return {}
        
        entities = {}
        projects_and_groups = raw_config['projects_and_groups']
        
        for entity_path, entity_data in projects_and_groups.items():
            entities[entity_path] = self._parse_entity(entity_path, entity_data)
        
        return entities
    
    def parse_file(self, file_path: str) -> Dict[str, EntityConfig]:
        """
        Parse a configuration file into EntityConfig objects.
        
        Args:
            file_path: Path to YAML configuration file
            
        Returns:
            Dictionary mapping entity paths to EntityConfig objects
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            return self.parse(f.read())
    
    def _parse_entity(self, path: str, data: Any) -> EntityConfig:
        """
        Parse a single entity (group or project) configuration.
        
        Args:
            path: Entity path (e.g., "group/*" or "group/project")
            data: Configuration data for the entity
            
        Returns:
            EntityConfig object
        """
        entity = EntityConfig(path=path)
        
        # Extract control directives at entity level
        entity._enforce = self._get_tag(data, 'enforce', False)
        entity._inherit = self._get_tag(data, 'inherit', None)
        
        # Parse each section
        data_dict = self._to_dict(data)
        
        if 'project_settings' in data_dict:
            entity.project_settings = self._parse_project_settings(data_dict['project_settings'])
        
        if 'group_settings' in data_dict:
            entity.group_settings = self._parse_group_settings(data_dict['group_settings'])
        
        if 'badges' in data_dict:
            entity.badges = self._parse_badges(data_dict['badges'])
        
        if 'group_badges' in data_dict:
            entity.group_badges = self._parse_badges(data_dict['group_badges'])
        
        if 'project_push_rules' in data_dict:
            entity.project_push_rules = self._parse_push_rules(data_dict['project_push_rules'])
        
        if 'group_push_rules' in data_dict:
            entity.group_push_rules = self._parse_push_rules(data_dict['group_push_rules'])
        
        if 'members' in data_dict:
            entity.members = self._parse_members(data_dict['members'])
        
        if 'group_members' in data_dict:
            entity.group_members = self._parse_members(data_dict['group_members'])
        
        if 'deploy_keys' in data_dict:
            entity.deploy_keys = self._parse_deploy_keys(data_dict['deploy_keys'])
        
        if 'variables' in data_dict:
            entity.variables = self._parse_variables(data_dict['variables'])
        
        if 'labels' in data_dict:
            entity.labels = self._parse_labels(data_dict['labels'])
        
        if 'webhooks' in data_dict:
            entity.webhooks = self._parse_webhooks(data_dict['webhooks'])
        
        if 'protected_branches' in data_dict:
            entity.protected_branches = self._parse_protected_branches(data_dict['protected_branches'])
        
        return entity
    
    def _parse_project_settings(self, data: Any) -> ProjectSettingsConfig:
        """Parse project settings configuration."""
        config = ProjectSettingsConfig()
        
        # Extract control directives
        config._enforce = self._get_tag(data, 'enforce', False)
        config._inherit = self._get_tag(data, 'inherit', None)
        config._delete = self._get_tag(data, 'delete', False)
        config._keep_existing = self._get_tag(data, 'keep_existing', False)
        
        data_dict = self._to_dict(data)
        
        # Extract raw parameters
        config.raw = self._extract_raw_parameters(data_dict)
        
        # Parse known fields
        if 'default_branch' in data_dict:
            config.default_branch = data_dict['default_branch']
        
        if 'visibility' in data_dict:
            vis = data_dict['visibility']
            config.visibility = Visibility(vis) if isinstance(vis, str) else vis
        
        if 'description' in data_dict:
            config.description = data_dict['description']
        
        if 'topics' in data_dict:
            topics_data = data_dict['topics']
            if isinstance(topics_data, list):
                config.topics = [
                    self._get_value(item) for item in topics_data
                ]
        
        if 'builds_access_level' in data_dict:
            config.builds_access_level = data_dict['builds_access_level']
        
        if 'only_allow_merge_if_pipeline_succeeds' in data_dict:
            config.only_allow_merge_if_pipeline_succeeds = data_dict['only_allow_merge_if_pipeline_succeeds']
        
        if 'only_allow_merge_if_all_discussions_are_resolved' in data_dict:
            config.only_allow_merge_if_all_discussions_are_resolved = data_dict['only_allow_merge_if_all_discussions_are_resolved']
        
        if 'remove_source_branch_after_merge' in data_dict:
            config.remove_source_branch_after_merge = data_dict['remove_source_branch_after_merge']
        
        if 'duo_features_enabled' in data_dict:
            config.duo_features_enabled = data_dict['duo_features_enabled']
        
        if 'container_expiration_policy_attributes' in data_dict:
            config.container_expiration_policy_attributes = data_dict['container_expiration_policy_attributes']
        
        # Store any additional settings not explicitly defined
        known_fields = {
            'default_branch', 'visibility', 'description', 'topics',
            'builds_access_level', 'only_allow_merge_if_pipeline_succeeds',
            'only_allow_merge_if_all_discussions_are_resolved',
            'remove_source_branch_after_merge', 'duo_features_enabled',
            'container_expiration_policy_attributes', 'raw'
        }
        config.additional_settings = {
            k: v for k, v in data_dict.items() if k not in known_fields
        }
        
        return config
    
    def _parse_group_settings(self, data: Any) -> GroupSettingsConfig:
        """Parse group settings configuration."""
        config = GroupSettingsConfig()
        
        # Extract control directives
        config._enforce = self._get_tag(data, 'enforce', False)
        config._inherit = self._get_tag(data, 'inherit', None)
        
        data_dict = self._to_dict(data)
        
        # Extract raw parameters
        config.raw = self._extract_raw_parameters(data_dict)
        
        if 'name' in data_dict:
            config.name = data_dict['name']
        
        if 'path' in data_dict:
            config.path = data_dict['path']
        
        if 'description' in data_dict:
            config.description = data_dict['description']
        
        if 'visibility' in data_dict:
            vis = data_dict['visibility']
            config.visibility = Visibility(vis) if isinstance(vis, str) else vis
        
        # Store additional settings
        known_fields = {'name', 'path', 'description', 'visibility', 'raw'}
        config.additional_settings = {
            k: v for k, v in data_dict.items() if k not in known_fields
        }
        
        return config
    
    def _parse_badges(self, data: Any) -> BadgesConfig:
        """Parse badges configuration."""
        config = BadgesConfig()
        
        # Extract control directives
        config._enforce = self._get_tag(data, 'enforce', False)
        config._inherit = self._get_tag(data, 'inherit', None)
        config._keep_existing = self._get_tag(data, 'keep_existing', False)
        
        data_dict = self._to_dict(data)
        
        # Extract raw parameters
        config.raw = self._extract_raw_parameters(data_dict)
        
        for badge_name, badge_data in data_dict.items():
            if badge_name in CONTROL_KEYS:
                # Skip old-style control keys
                continue
            
            badge_dict = self._to_dict(badge_data)
            badge = BadgeConfig(
                name=badge_dict.get('name', badge_name),
                link_url=badge_dict.get('link_url'),
                image_url=badge_dict.get('image_url'),
                delete=badge_dict.get('delete', False)
            )
            badge._delete = self._get_tag(badge_data, 'delete', badge.delete)
            badge.raw = badge_dict.get('raw', {})
            
            config.badges[badge_name] = badge
        
        return config
    
    def _parse_members(self, data: Any) -> MembersConfig:
        """Parse members configuration."""
        config = MembersConfig()
        
        # Extract control directives
        config._enforce = self._get_tag(data, 'enforce', False)
        config._inherit = self._get_tag(data, 'inherit', None)
        
        data_dict = self._to_dict(data)
        
        # Extract raw parameters
        config.raw = self._extract_raw_parameters(data_dict)
        
        if 'users' in data_dict:
            users_data = data_dict['users']
            users_dict = self._to_dict(users_data)
            
            for username, user_data in users_dict.items():
                user_dict = self._to_dict(user_data)
                access_level = user_dict.get('access_level', AccessLevel.DEVELOPER)
                if isinstance(access_level, str):
                    try:
                        access_level = AccessLevel(access_level)
                    except ValueError:
                        pass  # Keep as string if not a valid enum value
                member = MemberConfig(
                    access_level=access_level,
                    expires_at=user_dict.get('expires_at')
                )
                member._delete = self._get_tag(user_data, 'delete', False)
                member.raw = user_dict.get('raw', {})
                config.users[username] = member
        
        if 'groups' in data_dict:
            config.groups = self._to_dict(data_dict['groups'])
        
        return config
    
    def _parse_deploy_keys(self, data: Any) -> DeployKeysConfig:
        """Parse deploy keys configuration."""
        config = DeployKeysConfig()
        
        # Extract control directives
        config._enforce = self._get_tag(data, 'enforce', False)
        config._inherit = self._get_tag(data, 'inherit', None)
        
        data_dict = self._to_dict(data)
        
        # Extract raw parameters
        config.raw = self._extract_raw_parameters(data_dict)
        
        for key_name, key_data in data_dict.items():
            key_dict = self._to_dict(key_data)
            key = DeployKeyConfig(
                key=key_dict['key'],
                title=key_dict['title'],
                can_push=key_dict.get('can_push', False)
            )
            key._delete = self._get_tag(key_data, 'delete', False)
            key.raw = key_dict.get('raw', {})
            config.keys[key_name] = key
        
        return config
    
    def _parse_variables(self, data: Any) -> VariablesConfig:
        """Parse variables configuration."""
        config = VariablesConfig()
        
        # Extract control directives
        config._enforce = self._get_tag(data, 'enforce', False)
        config._inherit = self._get_tag(data, 'inherit', None)
        
        data_dict = self._to_dict(data)
        
        # Extract raw parameters
        config.raw = self._extract_raw_parameters(data_dict)
        
        for var_name, var_data in data_dict.items():
            var_dict = self._to_dict(var_data)
            variable = VariableConfig(
                value=var_dict['value'],
                masked=var_dict.get('masked', False),
                protected=var_dict.get('protected', False),
                variable_type=var_dict.get('variable_type', 'env_var')
            )
            variable._delete = self._get_tag(var_data, 'delete', False)
            variable.raw = var_dict.get('raw', {})
            config.variables[var_name] = variable
        
        return config
    
    def _parse_labels(self, data: Any) -> LabelsConfig:
        """Parse labels configuration."""
        config = LabelsConfig()
        
        # Extract control directives
        config._enforce = self._get_tag(data, 'enforce', False)
        config._inherit = self._get_tag(data, 'inherit', None)
        
        data_dict = self._to_dict(data)
        
        # Extract raw parameters
        config.raw = self._extract_raw_parameters(data_dict)
        
        for label_name, label_data in data_dict.items():
            label_dict = self._to_dict(label_data)
            label = LabelConfig(
                color=label_dict['color'],
                description=label_dict.get('description'),
                priority=label_dict.get('priority')
            )
            label._delete = self._get_tag(label_data, 'delete', False)
            label.raw = label_dict.get('raw', {})
            config.labels[label_name] = label
        
        return config
    
    def _parse_webhooks(self, data: Any) -> WebhooksConfig:
        """Parse webhooks configuration."""
        config = WebhooksConfig()
        
        # Extract control directives
        config._enforce = self._get_tag(data, 'enforce', False)
        config._inherit = self._get_tag(data, 'inherit', None)
        
        data_dict = self._to_dict(data)
        
        # Extract raw parameters
        config.raw = self._extract_raw_parameters(data_dict)
        
        for hook_name, hook_data in data_dict.items():
            hook_dict = self._to_dict(hook_data)
            webhook = WebhookConfig(
                url=hook_dict['url'],
                token=hook_dict.get('token'),
                push_events=hook_dict.get('push_events', True),
                merge_requests_events=hook_dict.get('merge_requests_events', False),
                enable_ssl_verification=hook_dict.get('enable_ssl_verification', True)
            )
            webhook._delete = self._get_tag(hook_data, 'delete', False)
            webhook.raw = hook_dict.get('raw', {})
            config.webhooks[hook_name] = webhook
        
        return config
    
    def _parse_protected_branches(self, data: Any) -> ProtectedBranchesConfig:
        """Parse protected branches configuration."""
        config = ProtectedBranchesConfig()
        
        # Extract control directives
        config._enforce = self._get_tag(data, 'enforce', False)
        config._inherit = self._get_tag(data, 'inherit', None)
        
        data_dict = self._to_dict(data)
        
        # Extract raw parameters
        config.raw = self._extract_raw_parameters(data_dict)
        
        for branch_name, branch_data in data_dict.items():
            branch_dict = self._to_dict(branch_data)
            
            # Convert string access levels to enum
            push_level = branch_dict.get('push_access_level', AccessLevel.MAINTAINER)
            if isinstance(push_level, str):
                try:
                    push_level = AccessLevel(push_level)
                except ValueError:
                    pass
            
            merge_level = branch_dict.get('merge_access_level', AccessLevel.MAINTAINER)
            if isinstance(merge_level, str):
                try:
                    merge_level = AccessLevel(merge_level)
                except ValueError:
                    pass
            
            unprotect_level = branch_dict.get('unprotect_access_level')
            if isinstance(unprotect_level, str):
                try:
                    unprotect_level = AccessLevel(unprotect_level)
                except ValueError:
                    pass
            
            branch = ProtectedBranchConfig(
                push_access_level=push_level,
                merge_access_level=merge_level,
                unprotect_access_level=unprotect_level
            )
            branch._delete = self._get_tag(branch_data, 'delete', False)
            branch.raw = branch_dict.get('raw', {})
            config.branches[branch_name] = branch
        
        return config
    
    def _parse_push_rules(self, data: Any) -> PushRulesConfig:
        """Parse push rules configuration."""
        config = PushRulesConfig()
        
        # Extract control directives
        config._enforce = self._get_tag(data, 'enforce', False)
        config._inherit = self._get_tag(data, 'inherit', None)
        
        data_dict = self._to_dict(data)
        
        # Extract raw parameters
        config.raw = self._extract_raw_parameters(data_dict)
        
        # Parse known fields
        if 'commit_message_regex' in data_dict:
            config.commit_message_regex = data_dict['commit_message_regex']
        
        if 'commit_message_negative_regex' in data_dict:
            config.commit_message_negative_regex = data_dict['commit_message_negative_regex']
        
        if 'branch_name_regex' in data_dict:
            config.branch_name_regex = data_dict['branch_name_regex']
        
        if 'author_email_regex' in data_dict:
            config.author_email_regex = data_dict['author_email_regex']
        
        if 'file_name_regex' in data_dict:
            config.file_name_regex = data_dict['file_name_regex']
        
        if 'deny_delete_tag' in data_dict:
            config.deny_delete_tag = data_dict['deny_delete_tag']
        
        if 'member_check' in data_dict:
            config.member_check = data_dict['member_check']
        
        if 'prevent_secrets' in data_dict:
            config.prevent_secrets = data_dict['prevent_secrets']
        
        if 'commit_committer_check' in data_dict:
            config.commit_committer_check = data_dict['commit_committer_check']
        
        if 'commit_committer_name_check' in data_dict:
            config.commit_committer_name_check = data_dict['commit_committer_name_check']
        
        if 'max_file_size' in data_dict:
            config.max_file_size = data_dict['max_file_size']
        
        # Store additional settings
        known_fields = {
            'commit_message_regex', 'commit_message_negative_regex',
            'branch_name_regex', 'author_email_regex', 'file_name_regex',
            'deny_delete_tag', 'member_check', 'prevent_secrets',
            'commit_committer_check', 'commit_committer_name_check',
            'max_file_size', 'raw'
        }
        config.additional_settings = {
            k: v for k, v in data_dict.items() if k not in known_fields
        }
        
        return config
    
    def _get_tag(self, value: Any, tag_name: str, default: Any = None) -> Any:
        """Get a tag value from a tagged object."""
        if hasattr(value, 'get_tag'):
            return value.get_tag(tag_name, default)
        return default
    
    def _get_value(self, value: Any) -> Any:
        """Get the actual value from a potentially tagged object."""
        if isinstance(value, GitLabFormTagScalar):
            return value.value
        return value
    
    def _to_dict(self, value: Any) -> Dict[str, Any]:
        """Convert value to dictionary, handling tagged objects."""
        if isinstance(value, (GitLabFormTagOrderedDict, dict)):
            return dict(value)
        return {}
    
    def _extract_raw_parameters(self, data_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract raw parameters from configuration.
        
        Raw parameters are stored under the 'raw' key and will be passed
        directly to the GitLab API without validation.
        
        Args:
            data_dict: Configuration dictionary
            
        Returns:
            Dictionary of raw parameters (empty if none found)
        """
        return data_dict.get('raw', {})


def parse_typed_config_v5(config_string: str) -> Dict[str, EntityConfig]:
    """
    Convenience function to parse a v5 configuration string into typed objects.
    
    Args:
        config_string: YAML configuration as string
        
    Returns:
        Dictionary mapping entity paths to EntityConfig objects
        
    Example:
        >>> config = '''
        ... projects_and_groups:
        ...   mygroup/*:
        ...     project_settings: !inherit force
        ...     badges:
        ...       !enforce
        ...       coverage:
        ...         name: "Coverage"
        ...         link_url: "http://example.com"
        ... '''
        >>> entities = parse_typed_config_v5(config)
        >>> group_config = entities['mygroup/*']
        >>> group_config.project_settings.get_inheritance()
        'force'
        >>> group_config.badges.is_enforced()
        True
    """
    parser = ConfigV5TypedParser()
    return parser.parse(config_string)


def parse_typed_config_v5_file(file_path: str) -> Dict[str, EntityConfig]:
    """
    Convenience function to parse a v5 configuration file into typed objects.
    
    Args:
        file_path: Path to YAML configuration file
        
    Returns:
        Dictionary mapping entity paths to EntityConfig objects
    """
    parser = ConfigV5TypedParser()
    return parser.parse_file(file_path)
