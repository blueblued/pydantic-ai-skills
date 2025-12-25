"""pydantic-ai-sops: A tool-calling-based agent SOPs implementation for Pydantic AI.

This package provides a standardized, composable framework for building and managing
Agent SOPs within the Pydantic AI ecosystem. Agent SOPs are modular collections
of instructions, scripts, tools, and resources that enable AI agents to progressively
discover, load, and execute specialized capabilities for domain-specific tasks.

Example:
    ```python
    from pydantic_ai import Agent
    from pydantic_ai_sops import SOPsToolset

    # Initialize SOPs Toolset with one or more SOP directories
    sops_toolset = SOPsToolset(directories=["./sops"])

    # Create agent with SOPs as a toolset
    agent = Agent(
        model='openai:gpt-4o',
        instructions="You are a helpful research assistant.",
        toolsets=[sops_toolset]
    )

    # Add SOPs system prompt to agent
    @agent.system_prompt
    def add_sops_to_system_prompt() -> str:
        return sops_toolset.get_sops_system_prompt()

    # Use agent - SOPs tools are available for the agent to call
    result = await agent.run(
        "What are the last 3 papers on arXiv about machine learning?"
    )
    print(result.output)
    ```
"""

from pydantic_ai_sops.exceptions import (
    SOPException,
    SOPNotFoundError,
    SOPResourceLoadError,
    SOPScriptExecutionError,
    SOPValidationError,
)
from pydantic_ai_sops.toolset import SOPsToolset, discover_sops, parse_sop_md
from pydantic_ai_sops.types import SOP, SOPMetadata, SOPResource

__all__ = [
    # Main toolset
    'SOPsToolset',
    # Types
    'SOP',
    'SOPMetadata',
    'SOPResource',
    # Exceptions
    'SOPException',
    'SOPNotFoundError',
    'SOPResourceLoadError',
    'SOPScriptExecutionError',
    'SOPValidationError',
    # Utility functions
    'discover_sops',
    'parse_sop_md',
]
