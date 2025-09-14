"""UI components for Any Agent containers."""

# The UI system has been migrated to React SPA architecture.
# This module now serves as a compatibility layer and entry point
# for the React UI build system and manager.

from .manager import UIBuildManager

__all__ = [
    "UIBuildManager",
]
