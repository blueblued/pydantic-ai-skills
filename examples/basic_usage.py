"""Basic example demonstrating skill integration with Pydantic AI.

This example shows how to create an agent with skills and use them
for research tasks.
"""

import asyncio
from pathlib import Path

from pydantic_ai import Agent

from pydantic_ai_sops import SOPsToolset


async def main() -> None:
    """Pydantic AI with SOPs."""
    # Get the SOPs directory (examples/sops)
    sops_dir = Path(__file__).parent / 'sops'

    # Initialize SOPs Toolset
    sops_toolset = SOPsToolset(directories=[sops_dir])

    # Create agent with SOPs
    agent = Agent(
        model='openai:gpt-4o',
        instructions='You are a helpful research assistant.',
        toolsets=[sops_toolset],
    )

    # Add SOPs system prompt (includes SOP descriptions and usage)
    @agent.system_prompt
    async def add_sops_prompt() -> str:
        return sops_toolset.get_sops_system_prompt()

    user_prompt = 'What are the main features of Pydantic AI framework?'

    result = await agent.run(user_prompt)
    print(f'Response:\n\n{result.output}')


if __name__ == '__main__':
    asyncio.run(main())
