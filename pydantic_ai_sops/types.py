"""Type definitions for pydantic-ai-sops.

This module contains dataclass-based type definitions for SOPs,
their metadata, resources, and scripts.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SOPMetadata:
    """SOP metadata from SOP.md frontmatter.

    Only `name` and `description` are required. Other fields
    (version, author, category, tags, etc.) can be added dynamically
    based on frontmatter content.

    Attributes:
        name: The SOP identifier.
        description: Brief description of what the SOP does.
        extra: Additional metadata fields from frontmatter.
    """

    name: str
    description: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class SOPResource:
    """A resource file within a SOP (e.g., FORMS.md, REFERENCE.md).

    Attributes:
        name: Resource filename (e.g., "FORMS.md").
        path: Absolute path to the resource file.
        content: Loaded content (lazy-loaded, None until read).
    """

    name: str
    path: Path
    content: str | None = None


@dataclass
class SOPScript:
    """An executable script within a SOP.

    Script-based tools: Executable Python scripts in scripts/ directory
    or directly in the SOP directory.
    Can be executed via SOPsToolset.run_sop_script() tool.

    Attributes:
        name: Script name without .py extension.
        path: Absolute path to the script file.
        sop_name: Parent SOP name.
    """

    name: str
    path: Path
    sop_name: str


@dataclass
class SOP:
    """A loaded SOP instance.

    Attributes:
        name: SOP name (from metadata).
        path: Absolute path to SOP directory.
        metadata: Parsed metadata from SOP.md.
        content: Main content from SOP.md (without frontmatter).
        resources: Optional resource files (FORMS.md, etc.).
        scripts: Available scripts in the SOP directory or scripts/ subdirectory.
    """

    name: str
    path: Path
    metadata: SOPMetadata
    content: str
    resources: list[SOPResource] = field(default_factory=list)
    scripts: list[SOPScript] = field(default_factory=list)

    @property
    def description(self) -> str:
        """Get SOP description from metadata."""
        return self.metadata.description
