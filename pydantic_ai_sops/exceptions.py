"""Exception classes for pydantic-ai-sops."""


class SOPException(Exception):
    """Base exception for SOP-related errors."""


class SOPNotFoundError(SOPException):
    """SOP not found in any source."""


class SOPValidationError(SOPException):
    """SOP validation failed."""


class SOPResourceLoadError(SOPException):
    """Failed to load SOP resources."""


class SOPScriptExecutionError(SOPException):
    """SOP script execution failed."""
