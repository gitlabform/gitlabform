"""
Typed configuration objects for GitLabForm v5.

This module defines specific configuration classes for each configuration section
(badges, project_settings, push_rules, etc.) as documented in docs/reference.
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum

from gitlabform.configuration.config_v5_base import (
    InheritMixin,
    EnforceMixin,
    DeleteMixin,
    KeepExistingMixin,
    RawParametersMixin,
    FullControlDirectives,
    ConfigWithRaw,
)


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
class BadgeConfig(ConfigWithRaw):
    """Configuration for a single badge."""
    name: str = ""
    link_url: Optional[str] = None
    image_url: Optional[str] = None
    delete: bool = False


@dataclass
class BadgesConfig(InheritMixin, EnforceMixin, KeepExistingMixin, RawParametersMixin):
    """Configuration for badges (project or group)."""
    badges: Dict[str, BadgeConfig] = field(default_factory=dict)


@dataclass
class ProjectSettingsConfig(ConfigWithRaw):
    """
    Configuration for project settings.
    
    Supports raw parameters passing - any parameters in the 'raw' dict
    will be passed directly to the GitLab API without validation.
    """
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
    
    # Additional settings (deprecated - use 'raw' instead)
    additional_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GroupSettingsConfig(ConfigWithRaw):
    """
    Configuration for group settings.
    
    Supports raw parameters passing - any parameters in the 'raw' dict
    will be passed directly to the GitLab API without validation.
    """
    # Group settings
    name: Optional[str] = None
    path: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[Visibility] = None
    
    # Additional settings (deprecated - use 'raw' instead)
    additional_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemberConfig(DeleteMixin, RawParametersMixin):
    """Configuration for a single member."""
    access_level: Union[int, AccessLevel] = AccessLevel.DEVELOPER
    expires_at: Optional[str] = None


@dataclass
class MembersConfig(InheritMixin, EnforceMixin, RawParametersMixin):
    """Configuration for members (project or group)."""
    users: Dict[str, MemberConfig] = field(default_factory=dict)
    groups: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class DeployKeyConfig(DeleteMixin, RawParametersMixin):
    """Configuration for a single deploy key."""
    key: str = ""
    title: str = ""
    can_push: bool = False


@dataclass
class DeployKeysConfig(InheritMixin, EnforceMixin, RawParametersMixin):
    """Configuration for deploy keys."""
    keys: Dict[str, DeployKeyConfig] = field(default_factory=dict)


@dataclass
class VariableConfig(DeleteMixin, RawParametersMixin):
    """
    Configuration for a CI/CD variable.
    
    Note: The 'raw' parameter in VariableConfig corresponds to GitLab's
    'raw' field which controls variable expansion, not raw parameters.
    Use the 'raw' dict in RawParametersMixin for additional parameters.
    """
    value: str = ""
    masked: bool = False
    protected: bool = False
    variable_type: str = "env_var"


@dataclass
class VariablesConfig(InheritMixin, EnforceMixin, RawParametersMixin):
    """Configuration for CI/CD variables."""
    variables: Dict[str, VariableConfig] = field(default_factory=dict)


@dataclass
class LabelConfig(DeleteMixin, RawParametersMixin):
    """Configuration for a label."""
    color: str = "#000000"
    description: Optional[str] = None
    priority: Optional[int] = None


@dataclass
class LabelsConfig(InheritMixin, EnforceMixin, RawParametersMixin):
    """Configuration for labels."""
    labels: Dict[str, LabelConfig] = field(default_factory=dict)


@dataclass
class WebhookConfig(DeleteMixin, RawParametersMixin):
    """Configuration for a webhook."""
    url: str = ""
    token: Optional[str] = None
    push_events: bool = True
    merge_requests_events: bool = False
    enable_ssl_verification: bool = True


@dataclass
class WebhooksConfig(InheritMixin, EnforceMixin, RawParametersMixin):
    """Configuration for webhooks."""
    webhooks: Dict[str, WebhookConfig] = field(default_factory=dict)


@dataclass
class ProtectedBranchConfig(DeleteMixin, RawParametersMixin):
    """Configuration for a protected branch."""
    push_access_level: Union[int, AccessLevel] = AccessLevel.MAINTAINER
    merge_access_level: Union[int, AccessLevel] = AccessLevel.MAINTAINER
    unprotect_access_level: Optional[Union[int, AccessLevel]] = None


@dataclass
class ProtectedBranchesConfig(InheritMixin, EnforceMixin, RawParametersMixin):
    """Configuration for protected branches."""
    branches: Dict[str, ProtectedBranchConfig] = field(default_factory=dict)


@dataclass
class PushRulesConfig(ConfigWithRaw):
    """
    Configuration for push rules (project or group).
    
    Supports raw parameters passing - any parameters in the 'raw' dict
    will be passed directly to the GitLab API without validation.
    """
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
    
    # Additional settings (deprecated - use 'raw' instead)
    additional_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FilesConfig(ConfigWithRaw):
    """Configuration for files in the repository."""
    files: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BranchesConfig(ConfigWithRaw):
    """Configuration for repository branches."""
    branches: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TagsConfig(ConfigWithRaw):
    """Configuration for repository tags protection."""
    tags: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrationsConfig(ConfigWithRaw):
    """Configuration for project integrations (formerly services)."""
    integrations: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobTokenScopeConfig(ConfigWithRaw):
    """Configuration for CI/CD job token scope."""
    allowlist: Optional[List[str]] = None


@dataclass
class MergeRequestsApprovalRulesConfig(ConfigWithRaw):
    """Configuration for merge request approval rules."""
    rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MergeRequestsApprovalsConfig(ConfigWithRaw):
    """Configuration for merge request approvals."""
    approvals: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProtectedEnvironmentsConfig(ConfigWithRaw):
    """Configuration for protected environments."""
    environments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceGroupsConfig(ConfigWithRaw):
    """Configuration for resource groups."""
    resource_groups: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SchedulesConfig(ConfigWithRaw):
    """Configuration for pipeline schedules."""
    schedules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GroupLDAPLinksConfig(ConfigWithRaw):
    """Configuration for group LDAP links."""
    links: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GroupSAMLLinksConfig(ConfigWithRaw):
    """Configuration for group SAML links."""
    links: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GroupHooksConfig(InheritMixin, EnforceMixin, RawParametersMixin):
    """Configuration for group hooks."""
    hooks: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HooksConfig(InheritMixin, EnforceMixin, RawParametersMixin):
    """Configuration for project hooks (webhooks)."""
    hooks: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectSecuritySettingsConfig(ConfigWithRaw):
    """Configuration for project security settings."""
    # Add specific security settings as they're identified
    pass


@dataclass
class ApplicationSettingsConfig(ConfigWithRaw):
    """Configuration for GitLab application-wide settings."""
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectConfig(ConfigWithRaw):
    """Configuration for project creation/archiving/transfer operations."""
    archive: Optional[bool] = None
    unarchive: Optional[bool] = None


@dataclass
class EntityConfig(InheritMixin, EnforceMixin):
    """
    Complete configuration for a group or project entity.
    
    This contains all possible configuration sections that can be
    applied to a group or project.
    """
    # Project-specific sections
    project: Optional[ProjectConfig] = None
    project_settings: Optional[ProjectSettingsConfig] = None
    project_security_settings: Optional[ProjectSecuritySettingsConfig] = None
    badges: Optional[BadgesConfig] = None
    project_push_rules: Optional[PushRulesConfig] = None
    
    # Group-specific sections
    group_settings: Optional[GroupSettingsConfig] = None
    group_badges: Optional[BadgesConfig] = None
    group_push_rules: Optional[PushRulesConfig] = None
    group_hooks: Optional[GroupHooksConfig] = None
    group_ldap_links: Optional[GroupLDAPLinksConfig] = None
    saml_group_links: Optional[GroupSAMLLinksConfig] = None
    group_labels: Optional[LabelsConfig] = None
    group_variables: Optional[VariablesConfig] = None
    
    # Common sections (both project and group)
    members: Optional[MembersConfig] = None
    group_members: Optional[MembersConfig] = None
    deploy_keys: Optional[DeployKeysConfig] = None
    variables: Optional[VariablesConfig] = None
    labels: Optional[LabelsConfig] = None
    webhooks: Optional[WebhooksConfig] = None
    hooks: Optional[HooksConfig] = None
    protected_branches: Optional[ProtectedBranchesConfig] = None
    branches: Optional[BranchesConfig] = None
    tags: Optional[TagsConfig] = None
    files: Optional[FilesConfig] = None
    integrations: Optional[IntegrationsConfig] = None
    job_token_scope: Optional[JobTokenScopeConfig] = None
    merge_requests_approvals: Optional[MergeRequestsApprovalsConfig] = None
    merge_requests_approval_rules: Optional[MergeRequestsApprovalRulesConfig] = None
    protected_environments: Optional[ProtectedEnvironmentsConfig] = None
    resource_groups: Optional[ResourceGroupsConfig] = None
    schedules: Optional[SchedulesConfig] = None
    settings: Optional[ApplicationSettingsConfig] = None
    
    # Entity path
    path: str = ""
    
    # Config attribute names for efficient lookup
    _CONFIG_ATTRS = [
        'project', 'project_settings', 'project_security_settings',
        'badges', 'project_push_rules',
        'group_settings', 'group_badges', 'group_push_rules', 'group_hooks',
        'group_ldap_links', 'saml_group_links', 'group_labels', 'group_variables',
        'members', 'group_members', 'deploy_keys', 'variables',
        'labels', 'webhooks', 'hooks', 'protected_branches', 'branches',
        'tags', 'files', 'integrations', 'job_token_scope',
        'merge_requests_approvals', 'merge_requests_approval_rules',
        'protected_environments', 'resource_groups', 'schedules', 'settings'
    ]
    
    def get_configs(self) -> List[Any]:
        """
        Get all non-None configuration objects.
        
        Returns:
            List of configuration objects that are set
        """
        configs = []
        for attr_name in self._CONFIG_ATTRS:
            attr = getattr(self, attr_name, None)
            if attr is not None:
                configs.append(attr)
        return configs
    
    def is_project(self) -> bool:
        """Check if this is a project configuration (not ending with /*)."""
        return not self.path.endswith('/*')
    
    def is_group(self) -> bool:
        """Check if this is a group configuration (ending with /*)."""
        return self.path.endswith('/*')
