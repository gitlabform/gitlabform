"""
Typed configuration objects for GitLabForm v5.

This module defines specific configuration classes for each configuration section
(badges, project_settings, push_rules, etc.) as documented in docs/reference.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum


class AccessLevel(str, Enum):
    """Access levels for members."""
    NO_ACCESS = "no_access"
    MINIMAL = "minimal"
    GUEST = "guest"
    REPORTER = "reporter"
    DEVELOPER = "developer"
    MAINTAINER = "maintainer"
    OWNER = "owner"
    ADMIN = "admin"


class Visibility(str, Enum):
    """Project visibility levels."""
    PRIVATE = "private"
    INTERNAL = "internal"
    PUBLIC = "public"


@dataclass
class BadgeConfig:
    """Configuration for a single badge."""
    name: str
    link_url: Optional[str] = None
    image_url: Optional[str] = None
    delete: bool = False
    
    # Control directives
    _enforce: bool = False
    _delete: bool = False
    _inherit: Optional[str] = None
    _keep_existing: bool = False


@dataclass
class BadgesConfig:
    """Configuration for badges (project or group)."""
    badges: Dict[str, BadgeConfig] = field(default_factory=dict)
    
    # Control directives
    _enforce: bool = False
    _inherit: Optional[str] = None
    _keep_existing: bool = False
    
    def is_enforced(self) -> bool:
        """Check if badges are enforced."""
        return self._enforce
    
    def get_inheritance(self) -> Optional[str]:
        """Get inheritance mode."""
        return self._inherit


@dataclass
class ProjectSettingsConfig:
    """Configuration for project settings."""
    # Common settings
    default_branch: Optional[str] = None
    visibility: Optional[Visibility] = None
    description: Optional[str] = None
    topics: Optional[List[str]] = None
    
    # Build settings
    builds_access_level: Optional[str] = None
    
    # Merge request settings
    only_allow_merge_if_pipeline_succeeds: Optional[bool] = None
    only_allow_merge_if_all_discussions_are_resolved: Optional[bool] = None
    remove_source_branch_after_merge: Optional[bool] = None
    
    # Features
    duo_features_enabled: Optional[bool] = None
    
    # Container registry
    container_expiration_policy_attributes: Optional[Dict[str, Any]] = None
    
    # Additional settings
    additional_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Control directives
    _enforce: bool = False
    _delete: bool = False
    _inherit: Optional[str] = None
    _keep_existing: bool = False
    
    def is_enforced(self) -> bool:
        """Check if project settings are enforced."""
        return self._enforce
    
    def get_inheritance(self) -> Optional[str]:
        """Get inheritance mode."""
        return self._inherit
    
    def should_delete(self) -> bool:
        """Check if marked for deletion."""
        return self._delete


@dataclass
class GroupSettingsConfig:
    """Configuration for group settings."""
    # Group settings
    name: Optional[str] = None
    path: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[Visibility] = None
    
    # Additional settings
    additional_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Control directives
    _enforce: bool = False
    _inherit: Optional[str] = None
    
    def is_enforced(self) -> bool:
        """Check if group settings are enforced."""
        return self._enforce
    
    def get_inheritance(self) -> Optional[str]:
        """Get inheritance mode."""
        return self._inherit


@dataclass
class MemberConfig:
    """Configuration for a single member."""
    access_level: Union[int, AccessLevel]
    expires_at: Optional[str] = None
    
    # Control directives
    _delete: bool = False


@dataclass
class MembersConfig:
    """Configuration for members (project or group)."""
    users: Dict[str, MemberConfig] = field(default_factory=dict)
    groups: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Control directives
    _enforce: bool = False
    _inherit: Optional[str] = None
    
    def is_enforced(self) -> bool:
        """Check if members are enforced."""
        return self._enforce
    
    def get_inheritance(self) -> Optional[str]:
        """Get inheritance mode."""
        return self._inherit


@dataclass
class DeployKeyConfig:
    """Configuration for a single deploy key."""
    key: str
    title: str
    can_push: bool = False
    
    # Control directives
    _delete: bool = False


@dataclass
class DeployKeysConfig:
    """Configuration for deploy keys."""
    keys: Dict[str, DeployKeyConfig] = field(default_factory=dict)
    
    # Control directives
    _enforce: bool = False
    _inherit: Optional[str] = None
    
    def is_enforced(self) -> bool:
        """Check if deploy keys are enforced."""
        return self._enforce


@dataclass
class VariableConfig:
    """Configuration for a CI/CD variable."""
    value: str
    masked: bool = False
    protected: bool = False
    variable_type: str = "env_var"
    
    # Control directives
    _delete: bool = False


@dataclass
class VariablesConfig:
    """Configuration for CI/CD variables."""
    variables: Dict[str, VariableConfig] = field(default_factory=dict)
    
    # Control directives
    _enforce: bool = False
    _inherit: Optional[str] = None
    
    def is_enforced(self) -> bool:
        """Check if variables are enforced."""
        return self._enforce


@dataclass
class LabelConfig:
    """Configuration for a label."""
    color: str
    description: Optional[str] = None
    priority: Optional[int] = None
    
    # Control directives
    _delete: bool = False


@dataclass
class LabelsConfig:
    """Configuration for labels."""
    labels: Dict[str, LabelConfig] = field(default_factory=dict)
    
    # Control directives
    _enforce: bool = False
    _inherit: Optional[str] = None
    
    def is_enforced(self) -> bool:
        """Check if labels are enforced."""
        return self._enforce


@dataclass
class WebhookConfig:
    """Configuration for a webhook."""
    url: str
    token: Optional[str] = None
    push_events: bool = True
    merge_requests_events: bool = False
    enable_ssl_verification: bool = True
    
    # Control directives
    _delete: bool = False


@dataclass
class WebhooksConfig:
    """Configuration for webhooks."""
    webhooks: Dict[str, WebhookConfig] = field(default_factory=dict)
    
    # Control directives
    _enforce: bool = False
    _inherit: Optional[str] = None
    
    def is_enforced(self) -> bool:
        """Check if webhooks are enforced."""
        return self._enforce


@dataclass
class ProtectedBranchConfig:
    """Configuration for a protected branch."""
    push_access_level: Union[int, AccessLevel] = AccessLevel.MAINTAINER
    merge_access_level: Union[int, AccessLevel] = AccessLevel.MAINTAINER
    unprotect_access_level: Optional[Union[int, AccessLevel]] = None
    
    # Control directives
    _delete: bool = False


@dataclass
class ProtectedBranchesConfig:
    """Configuration for protected branches."""
    branches: Dict[str, ProtectedBranchConfig] = field(default_factory=dict)
    
    # Control directives
    _enforce: bool = False
    _inherit: Optional[str] = None
    
    def is_enforced(self) -> bool:
        """Check if protected branches are enforced."""
        return self._enforce


@dataclass
class PushRulesConfig:
    """Configuration for push rules (project or group)."""
    # Commit rules
    commit_message_regex: Optional[str] = None
    commit_message_negative_regex: Optional[str] = None
    branch_name_regex: Optional[str] = None
    author_email_regex: Optional[str] = None
    file_name_regex: Optional[str] = None
    
    # Restrictions
    deny_delete_tag: Optional[bool] = None
    member_check: Optional[bool] = None
    prevent_secrets: Optional[bool] = None
    commit_committer_check: Optional[bool] = None
    commit_committer_name_check: Optional[bool] = None
    
    # Size
    max_file_size: Optional[int] = None
    
    # Additional settings
    additional_settings: Dict[str, Any] = field(default_factory=dict)
    
    # Control directives
    _enforce: bool = False
    _inherit: Optional[str] = None
    
    def is_enforced(self) -> bool:
        """Check if push rules are enforced."""
        return self._enforce
    
    def get_inheritance(self) -> Optional[str]:
        """Get inheritance mode."""
        return self._inherit


@dataclass
class EntityConfig:
    """
    Complete configuration for a group or project entity.
    
    This contains all possible configuration sections that can be
    applied to a group or project.
    """
    # Project-specific sections
    project_settings: Optional[ProjectSettingsConfig] = None
    badges: Optional[BadgesConfig] = None
    project_push_rules: Optional[PushRulesConfig] = None
    
    # Group-specific sections
    group_settings: Optional[GroupSettingsConfig] = None
    group_badges: Optional[BadgesConfig] = None
    group_push_rules: Optional[PushRulesConfig] = None
    
    # Common sections (both project and group)
    members: Optional[MembersConfig] = None
    group_members: Optional[MembersConfig] = None
    deploy_keys: Optional[DeployKeysConfig] = None
    variables: Optional[VariablesConfig] = None
    labels: Optional[LabelsConfig] = None
    webhooks: Optional[WebhooksConfig] = None
    protected_branches: Optional[ProtectedBranchesConfig] = None
    
    # Entity path
    path: str = ""
    
    # Control directives at entity level
    _enforce: bool = False
    _inherit: Optional[str] = None
    
    def get_configs(self) -> List[Any]:
        """
        Get all non-None configuration objects.
        
        Returns:
            List of configuration objects that are set
        """
        configs = []
        for attr_name in dir(self):
            if attr_name.startswith('_') or attr_name in ['path', 'get_configs', 'is_project', 'is_group']:
                continue
            attr = getattr(self, attr_name)
            if attr is not None and not callable(attr):
                configs.append(attr)
        return configs
    
    def is_project(self) -> bool:
        """Check if this is a project configuration (not ending with /*)."""
        return not self.path.endswith('/*')
    
    def is_group(self) -> bool:
        """Check if this is a group configuration (ending with /*)."""
        return self.path.endswith('/*')
