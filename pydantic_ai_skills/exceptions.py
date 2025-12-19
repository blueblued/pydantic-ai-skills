"""Exception classes for pydantic-ai-skills."""


class SkillException(Exception):
    """Base exception for skill-related errors."""


class SkillNotFoundError(SkillException):
    """Skill not found in any source."""


class SkillValidationError(SkillException):
    """Skill validation failed."""


class SkillResourceLoadError(SkillException):
    """Failed to load skill resources."""


class SkillScriptExecutionError(SkillException):
    """Skill script execution failed."""
