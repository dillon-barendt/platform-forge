"""Application-specific exceptions."""


class PlatformForgeError(RuntimeError):
    """Base exception for expected Platform Forge failures."""


class ConfigurationError(PlatformForgeError):
    """Raised when user-provided scaffold configuration is invalid."""
