"""SOPs toolset for pydantic-ai-sops.

SOPs are modular packages that extend agent capabilities. Each SOP is a folder
containing a SOP.md file with YAML frontmatter and Markdown instructions, along
with optional resource files (documents, scripts, etc.).

Progressive disclosure: Only SOP metadata is exposed initially. The full
instructions are loaded on-demand when the agent calls the activate_sop tool.

This module provides:
- SOPsToolset: A Pydantic AI toolset with four tools for SOP management
- SOP discovery from filesystem directories
- YAML frontmatter parsing for SOP.md files
- Safe script execution with path validation
"""

from __future__ import annotations

import logging
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import anyio
import yaml

import importlib
import os    


from pydantic_ai import RunContext
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.toolsets import FunctionToolset

from pydantic_ai_sops.exceptions import (
    SOPNotFoundError,
    SOPResourceLoadError,
    SOPScriptExecutionError,
    SOPValidationError,
)
from pydantic_ai_sops.types import (
    SOP,
    SOPMetadata,
    SOPResource
)

logger = logging.getLogger('pydantic-ai-sops')

# Anthropic's naming convention: lowercase letters, numbers, and hyphens only
SOP_NAME_PATTERN = re.compile(r'^[a-z0-9-]+$')
RESERVED_WORDS = {'anthropic', 'claude'}


def _validate_sop_metadata(
    frontmatter: dict[str, Any],
    instructions: str,
) -> list[str]:
    """Validate SOP metadata against Anthropic's requirements.

    Args:
        frontmatter: Parsed YAML frontmatter.
        instructions: The SOP instructions content.

    Returns:
        List of validation warnings (empty if no issues).
    """
    warnings_list = []

    name = frontmatter.get('name', '')
    description = frontmatter.get('description', '')

    # Validate name format
    if name:
        # Check length first to prevent regex on excessively long strings
        if len(name) > 64:
            warnings_list.append(f"SOP name '{name}' exceeds 64 characters ({len(name)} chars)")
        # Only run regex if name is reasonable length (defense in depth)
        elif not SOP_NAME_PATTERN.match(name):
            warnings_list.append(f"SOP name '{name}' should contain only lowercase letters, numbers, and hyphens")
        # Check for reserved words
        for reserved in RESERVED_WORDS:
            if reserved in name:
                warnings_list.append(f"SOP name '{name}' contains reserved word '{reserved}'")

    # Validate description
    if description and len(description) > 1024:
        warnings_list.append(f'SOP description exceeds 1024 characters ({len(description)} chars)')

    # Validate instructions length (Anthropic recommends under 500 lines)
    lines = instructions.split('\n')
    if len(lines) > 500:
        warnings_list.append(
            f'SOP.md body exceeds recommended 500 lines ({len(lines)} lines). '
            f'Consider splitting into separate resource files.'
        )

    return warnings_list


def parse_sop_md(content: str) -> tuple[dict[str, Any], str]:
    """Parse a SOP.md file into frontmatter and instructions.

    Uses PyYAML for robust YAML parsing.

    Args:
        content: Full content of the SOP.md file.

    Returns:
        Tuple of (frontmatter_dict, instructions_markdown).

    Raises:
        SOPValidationError: If YAML parsing fails.
    """
    # Match YAML frontmatter between --- delimiters
    frontmatter_pattern = r'^---\s*\n(.*?)^---\s*\n'
    match = re.search(frontmatter_pattern, content, re.DOTALL | re.MULTILINE)

    if not match:
        # No frontmatter, treat entire content as instructions
        return {}, content.strip()

    frontmatter_yaml = match.group(1).strip()
    instructions = content[match.end() :].strip()

    # Handle empty frontmatter
    if not frontmatter_yaml:
        return {}, instructions

    try:
        frontmatter = yaml.safe_load(frontmatter_yaml)
        if frontmatter is None:
            frontmatter = {}
    except yaml.YAMLError as e:
        raise SOPValidationError(f'Failed to parse YAML frontmatter: {e}') from e

    return frontmatter, instructions


def _discover_resources(sop_folder: Path) -> list[SOPResource]:
    """Discover resource files in a SOP folder.

    Resources are markdown files other than SOP.md, plus any files
    in a resources/ subdirectory.

    Args:
        sop_folder: Path to the SOP directory.

    Returns:
        List of discovered SOPResource objects.
    """
    resources: list[SOPResource] = []

    # Find .md files other than SOP.md (FORMS.md, REFERENCE.md, etc.)
    for md_file in sop_folder.glob('*.md'):
        if md_file.name.upper() != 'SOP.MD':
            resources.append(
                SOPResource(
                    name=md_file.name,
                    path=md_file.resolve(),
                )
            )

    # Find files in resources/ subdirectory if it exists
    resources_dir = sop_folder / 'resources'
    if resources_dir.exists() and resources_dir.is_dir():
        for resource_file in resources_dir.rglob('*'):
            if resource_file.is_file():
                rel_path = resource_file.relative_to(sop_folder)
                resources.append(
                    SOPResource(
                        name=str(rel_path),
                        path=resource_file.resolve(),
                    )
                )

    return resources


def _check_toolset(sop_folder: Path, sop_name: str) -> bool:
    """Check if a SOP folder contains a toolset(toolset.py).

    Args:
        sop_folder: Path to the SOP directory.
        sop_name: Name of the parent SOP.

    Returns:
        True if a toolset is found, False otherwise.
    """
    # Check if there is a toolset.py file in SOP folder root
    if (sop_folder / 'tools' / 'toolset.py').exists():
        return True
    return False

def discover_sops(
    directories: Sequence[str | Path],
    validate: bool = True,
) -> list[SOP]:
    """Discover SOPs from filesystem directories.

    Searches for SOP.md files in the given directories and loads
    SOP metadata and structure.

    Args:
        directories: List of directory paths to search for SOPs.
        validate: Whether to validate SOP structure (requires name and description).

    Returns:
        List of discovered SOP objects.

    Raises:
        SOPValidationError: If validation is enabled and a SOP is invalid.
    """
    sops: list[SOP] = []

    for sop_dir in directories:
        dir_path = Path(sop_dir).expanduser().resolve()

        if not dir_path.exists():
            logger.warning('SOPs directory does not exist: %s', dir_path)
            continue

        if not dir_path.is_dir():
            logger.warning('SOPs path is not a directory: %s', dir_path)
            continue

        # Find all SOP.md files (recursive search)
        for sop_file in dir_path.glob('**/SOP.md'):
            try:
                sop_folder = sop_file.parent
                content = sop_file.read_text(encoding='utf-8')
                frontmatter, instructions = parse_sop_md(content)

                # Get required fields
                name = frontmatter.get('name')
                description = frontmatter.get('description', '')

                # Validation
                if validate:
                    if not name:
                        logger.warning(
                            'SOP at %s missing required "name" field, skipping',
                            sop_folder,
                        )
                        continue
                    if not description:
                        logger.warning(
                            'SOP "%s" at %s missing "description" field',
                            name,
                            sop_folder,
                        )

                # Use folder name if name not provided
                if not name:
                    name = sop_folder.name

                # Extract extra metadata fields
                extra = {k: v for k, v in frontmatter.items() if k not in ('name', 'description')}

                # Create metadata
                metadata = SOPMetadata(
                    name=name,
                    description=description,
                    extra=extra,
                )

                # Validate metadata (log warnings)
                if validate:
                    validation_warnings = _validate_sop_metadata(frontmatter, instructions)
                    for warning in validation_warnings:
                        logger.warning('SOP "%s" at %s: %s', name, sop_folder, warning)

                # Discover resources and scripts
                resources = _discover_resources(sop_folder)
                has_toolset = _check_toolset(sop_folder, name)

                # Create SOP
                sop = SOP(
                    name=name,
                    path=sop_folder.resolve(),
                    metadata=metadata,
                    content=instructions,
                    has_toolset=has_toolset,
                    resources=resources
                )

                sops.append(sop)
                logger.debug('Discovered SOP: %s at %s', name, sop_folder)

            except SOPValidationError as e:
                logger.exception('SOP validation error in %s: %s', sop_file, e)
                raise
            except OSError as e:
                logger.warning('Failed to load SOP from %s: %s', sop_file, e)
                continue

    logger.info('Discovered %d SOPs from %d directories', len(sops), len(directories))
    return sops


def _is_safe_path(base_path: Path, target_path: Path) -> bool:
    """Check if target_path is safely within base_path (no path traversal).

    Args:
        base_path: The base directory path.
        target_path: The target path to validate.

    Returns:
        True if target_path is within base_path, False otherwise.
    """
    try:
        target_path.resolve().relative_to(base_path.resolve())
        return True
    except ValueError:
        return False

def _import_toolset(toolset_path: Path) -> FunctionToolset:
    """Import the toolset.py file and return a FunctionToolset object.
    """
    spec = importlib.util.spec_from_file_location(toolset_path.stem, str(toolset_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, 'sop_ts')

class SOPsToolset(FunctionToolset):
    """Pydantic AI toolset for automatic SOP discovery and integration.

    This is the primary interface for integrating SOPs with Pydantic AI agents.
    It implements the toolset protocol and automatically discovers, loads, and
    registers SOPs from specified directories.

    Provides the following tools to agents:
    - list_sops(): List all available SOPs
    - activate_sop(sop_name): Activate a SOP and load its instructions
    - read_sop_resource(sop_name, resource_name): Read a SOP resource file

    Example:
        ```python
        from pydantic_ai import Agent
        from pydantic_ai_sops import SOPsToolset

        sops_toolset = SOPsToolset(directories=["./sops"])

        agent = Agent(
            model='openai:gpt-4o',
            instructions="You are a helpful assistant.",
            toolsets=[sops_toolset]
        )

        @agent.system_prompt
        def add_sops_prompt() -> str:
            return sops_toolset.get_sops_system_prompt()
        ```
    """

    def __init__(
        self,
        directories: list[str | Path],
        *,
        auto_discover: bool = True,
        validate: bool = True,
        toolset_id: str = 'sops',
        script_timeout: int = 30,
        python_executable: str | Path | None = None,
    ) -> None:
        """Initialize the SOPs toolset.

        Args:
            directories: List of directory paths to search for SOPs.
            auto_discover: Automatically discover and load SOPs on init.
            validate: Validate SOP structure and metadata on load.
            toolset_id: Unique identifier for this toolset.
            script_timeout: Timeout in seconds for script execution (default: 30).
            python_executable: Path to Python executable for running scripts.
                If None, uses sys.executable (default).
        """
        super().__init__(id=toolset_id)

        self._directories = [Path(d) for d in directories]
        self._validate = validate
        self._script_timeout = script_timeout
        self._python_executable = str(python_executable) if python_executable else sys.executable
        self._sops: dict[str, SOP] = {}

        if auto_discover:
            self._discover_sops()

        # Register tools
        self._register_tools()

    def _discover_sops(self) -> None:
        """Discover and load SOPs from configured directories."""
        sops = discover_sops(
            directories=self._directories,
            validate=self._validate,
        )
        self._sops = {sop.name: sop for sop in sops}

    def _get_toolset(self, sop_name: str) -> FunctionToolset:
        """Load the python module toolset.py and return a FunctionToolset object.
        """
        toolset_path = self._sops[sop_name].path / 'tools' / 'toolset.py'
        toolset = _import_toolset(toolset_path)
        return toolset

    def _register_tools(self) -> None:  # noqa: C901
        """Register SOP management tools with the toolset.

        This method registers all four SOP management tools:
        - list_sops: List available SOPs
        - activate_sop: Activate a SOP and load its instructions
        - read_sop_resource: Read SOP resources
        """

        @self.tool
        async def list_sops(_ctx: RunContext[Any]) -> str:
            """List all available SOPs with their descriptions.

            Only use this tool if the available SOPs are not in your system prompt.

            Returns:
                Formatted list of available SOPs with names and descriptions.
            """
            if not self._sops:
                return 'No SOPs available.'

            lines = ['# Available SOPs', '']

            for name, sop in sorted(self._sops.items()):
                lines.append(f'{name}: {sop.metadata.description}')

            return '\n'.join(lines)

        @self.tool
        async def activate_sop(ctx: RunContext[Any], sop_name: str) -> str:  # noqa: D417
            """Activate a SOP and load its full instructions, making it the current available SOP.

            Always activate the SOP before using related tools or read_sop_resource
            to understand the SOP's capabilities, tools, available resources, and their usage patterns.

            Args:
                sop_name: Name of the SOP to activate.

            Returns:
                Full SOP instructions including available tools and resources.
            """
            _ = ctx  # Required by Pydantic AI toolset protocol
            if sop_name not in self._sops:
                available = ', '.join(sorted(self._sops.keys())) or 'none'
                return f"Error: SOP '{sop_name}' not found. Available SOPs: {available}"

            sop = self._sops[sop_name]
            logger.info('Activating SOP: %s', sop_name)

            lines = [
                f'# SOP: {sop.name}',
                f'**Description:** {sop.metadata.description}',
                f'**Path:** {sop.path}',
                '',
            ]

            # Add toolset if available
            if sop.has_toolset:
                lines.append('**Available Tools:**')
                sop_ts = self._get_toolset(sop_name)
                if hasattr(ctx.deps, 'state'): # 把激活的工具集传出来，以便在合适的时机调用
                    ctx.deps.state.sop_toolset = sop_ts
                
                for tool in sop_ts.tools.keys():
                    lines.append(f'- {tool}')
                lines.append('')

            # Add resource list if available
            if sop.resources:
                lines.append('**Available Resources:**')
                for resource in sop.resources:
                    lines.append(f'- {resource.name}')
                lines.append('')

            lines.append('---')
            lines.append('')
            lines.append(sop.content)

            return '\n'.join(lines)

        @self.tool
        async def read_sop_resource(  # noqa: D417
            ctx: RunContext[Any],
            sop_name: str,
            resource_name: str,
        ) -> str:
            """Read a resource file from a SOP (e.g., FORMS.md, REFERENCE.md).

            Call activate_sop first to see which resources are available.

            Args:
                sop_name: Name of the SOP.
                resource_name: The resource filename (e.g., "FORMS.md").

            Returns:
                The resource file content.
            """
            _ = ctx  # Required by Pydantic AI toolset protocol
            if sop_name not in self._sops:
                return f"Error: SOP '{sop_name}' not found."

            sop = self._sops[sop_name]

            # Find the resource
            resource = None
            for r in sop.resources:
                if r.name == resource_name:
                    resource = r
                    break

            if resource is None:
                available = [r.name for r in sop.resources]
                return (
                    f"Error: Resource '{resource_name}' not found in SOP '{sop_name}'. "
                    f'Available resources: {available}'
                )

            # Security check
            if not _is_safe_path(sop.path, resource.path):
                logger.warning('Path traversal attempt detected: %s in %s', resource_name, sop_name)
                return 'Error: Resource path escapes SOP directory.'

            try:
                content = resource.path.read_text(encoding='utf-8')
                logger.info('Read resource: %s from SOP %s', resource_name, sop_name)
                return content
            except OSError as e:
                logger.error('Failed to read resource %s: %s', resource_name, e)
                raise SOPResourceLoadError(f"Failed to read resource '{resource_name}': {e}") from e

    def get_sops_system_prompt(self) -> str:
        """Get the combined system prompt from all loaded SOPs.

        This should be added to the agent's system prompt to provide
        SOP discovery and usage instructions.

        Following Anthropic's approach, this includes all SOP metadata upfront
        in the system prompt, enabling the agent to discover and select SOPs
        without needing to call list_sops() first.

        Returns:
            Formatted system prompt containing:
            - All SOP metadata (name + description)
            - Instructions for using SOP tools
            - Progressive disclosure guidance
        """
        if not self._sops:
            return ''

        lines = [
            '# SOPs(Standard Operating Procedures)',
            '',
            'You have access to SOPs that extend your capabilities. ',
            'SOPs are modular packages containing instructions, resources, and toolset for specialized tasks.',
            'SOPs are in standby mode by default. You must use the `activate_sop` tool to activate a SOP and make it the current available SOP.',
            '**State management**: Only one SOP can be available at a time. When you activate a new SOP, it becomes the current available SOP and the SOP\'s tools become available to you.',
            '',
            '**You CANNOT call SOPs directly. You MUST use SOP tools to interact with SOPs. You can use `list_sops()` to list all available SOPs.**',
            '- `activate_sop(sop_name)` - to activate a SOP (load its instructions and make it the current available SOP and its tools become available to you)',
            '- `read_sop_resource(sop_name, resource_name)` - to read SOP resources',
            '',
            '## Standby SOPs',
            '',
            'The following SOPs are in standby mode:',
            '',
        ]

        # List all SOPs with descriptions and script parameters
        for name, sop in sorted(self._sops.items()):
            lines.append(f'- **{name}**: {sop.metadata.description}')
            # # Extract script arguments from SOP content
            # if sop.scripts:
            #     for script in sop.scripts:
            #         script_args = self._extract_script_args(sop.content, script.name)
            #         if script_args:
            #             lines.append(f'  - Script `{script.name}` parameters: {script_args}')

        lines.extend(
            [
                '## How to Use SOPs',
                '',
                '**REMINDER: SOPs are NOT callable. You MUST use SOP tools (activate_sop, read_sop_resource, etc.) to interact with SOPs.**',
                '',
                '**Progressive disclosure**: Activate SOPs only when needed.',
                '',
                '1. **When a SOP is relevant to the current task**: Use `activate_sop(sop_name)` to activate the SOP and read its full instructions.',
                '2. **For additional documentation**: Use `read_sop_resource(sop_name, resource_name)` to read FORMS.md, REFERENCE.md, or other resources.',
                '',
                '**CRITICAL: Parameter Requirements**',
                '',
                '**Best practices**:',
                '- Select SOPs based on task relevance and descriptions listed above',
                '- If you need more details, call `activate_sop(sop_name)` to activate and read full instructions and resources',
                '',
            ]
        )

        return '\n'.join(lines)

    @property
    def sops(self) -> dict[str, SOP]:
        """Get the dictionary of loaded SOPs.

        Returns:
            Dictionary mapping SOP names to SOP objects.
        """
        return self._sops

    def get_sop(self, name: str) -> SOP:
        """Get a specific SOP by name.

        Args:
            name: The SOP name.

        Returns:
            The SOP object.

        Raises:
            SOPNotFoundError: If the SOP is not found.
        """
        if name not in self._sops:
            raise SOPNotFoundError(f"SOP '{name}' not found")
        return self._sops[name]

    def refresh(self) -> None:
        """Re-discover SOPs from configured directories.

        Call this method to reload SOPs after changes to the filesystem.
        """
        logger.info('Refreshing SOPs from directories')
        self._discover_sops()
