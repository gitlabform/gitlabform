"""
Base classes for GitLabForm v5 configuration with control directives.

This module provides reusable base classes that implement control directives
(inherit, enforce, delete, keep_existing) and raw parameters support.
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class InheritMixin:
    """Mixin for configurations that support inheritance control."""
    _inherit: Optional[str] = None
    
    def get_inheritance(self) -> Optional[str]:
        """
        Get the inheritance mode for this configuration.
        
        Returns:
            One of: 'true', 'false', 'never', 'always', 'force', or None
        """
        return self._inherit


@dataclass
class EnforceMixin:
    """Mixin for configurations that support enforcement."""
    _enforce: bool = False
    
    def is_enforced(self) -> bool:
        """Check if this configuration is enforced."""
        return self._enforce


@dataclass
class DeleteMixin:
    """Mixin for configurations that can be marked for deletion."""
    _delete: bool = False
    
    def should_delete(self) -> bool:
        """Check if this configuration should be deleted."""
        return self._delete


@dataclass
class KeepExistingMixin:
    """Mixin for configurations that support keeping existing values."""
    _keep_existing: bool = False
    
    def should_keep_existing(self) -> bool:
        """Check if existing values should be kept when merging."""
        return self._keep_existing


@dataclass
class RawParametersMixin:
    """
    Mixin for configurations that support raw parameters.
    
    Raw parameters allow passing arbitrary key-value pairs directly
    to the GitLab API without validation or transformation.
    This is useful for new GitLab features not yet explicitly supported.
    """
    raw: Dict[str, Any] = field(default_factory=dict)
    
    def get_raw_parameters(self) -> Dict[str, Any]:
        """Get raw parameters to pass directly to GitLab API."""
        return self.raw
    
    def has_raw_parameters(self) -> bool:
        """Check if raw parameters are defined."""
        return bool(self.raw)


@dataclass
class FullControlDirectives(InheritMixin, EnforceMixin, DeleteMixin, KeepExistingMixin):
    """
    Base class with all control directives.
    
    This combines all control directive mixins for configurations
    that need full control over inheritance, enforcement, deletion,
    and keeping existing values.
    """
    pass


@dataclass
class ConfigWithRaw(FullControlDirectives, RawParametersMixin):
    """
    Base class with all control directives and raw parameters support.
    
    This is the most complete base class, providing all control directives
    plus support for raw parameter passing.
    """
    pass
