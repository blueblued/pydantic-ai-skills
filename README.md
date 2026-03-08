# pydantic-ai-sops

A lightweight SOP (Standard Operating Procedures) framework for Pydantic AI agents.

**SOPs** are modular packages containing instructions and toolsets that enable AI agents to progressively discover, activate, and execute specialized capabilities for domain-specific tasks.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Key Concepts

### SOP States

- **Available SOPs**: All SOPs installed and ready to be activated. They are in standby mode by default.
- **Active SOP**: The currently activated SOP. Only one SOP can be active at a time.
- **Standby SOPs**: Available SOPs that are not currently active.

### Progressive Disclosure

1. **Level 1 - Metadata**: All SOP names and descriptions are included in the system prompt
2. **Level 2 - Instructions**: Agent calls `activate_sop(name)` to load full instructions
3. **Level 3 - Resources**: Agent reads additional resources as needed

## Installation

```bash
pip install pydantic-ai-sops
```

## Quick Start

```python
from pydantic_ai import Agent
from pydantic_ai_sops import SOPsToolset

# Initialize SOPs Toolset with one or more SOP directories
sops_toolset = SOPsToolset(directories=["./sops"])

# Create agent with SOPs as a toolset
agent = Agent(
    model='openai:gpt-4o',
    instructions="You are a helpful assistant.",
    toolsets=[sops_toolset]
)

# Add SOPs system prompt to agent
@agent.system_prompt
async def add_sops_prompt() -> str:
    return sops_toolset.get_sops_system_prompt()

# Use agent
result = await agent.run("Help me with my research task.")
print(result.output)
```

## SOP Structure

### Basic Structure

```
my-sop/
└── SOP.md          # Required: Main instructions and metadata
```

### Extended Structure

```
my-sop/
├── SOP.md          # Required: Main instructions and metadata
├── FORMS.md        # Optional: Form-filling guides
├── REFERENCE.md    # Optional: Detailed reference
├── resources/      # Optional: Additional files
│   └── data.json
└── tools/
    └── toolset.py  # Optional: Dynamic toolset
```

### SOP.md Example

```markdown
---
name: my-sop
description: Brief description of what this SOP does and when to use it
---

# My SOP

## When to Use This SOP

Use this SOP when you need to:

- Do specific task A
- Handle scenario B

## Instructions

1. Step 1
2. Step 2
```

### Metadata Requirements

**Required fields:**
- `name`: SOP identifier (max 64 chars, lowercase letters/numbers/hyphens only)
- `description`: Brief description (max 1024 chars)

## Available Tools

The `SOPsToolset` provides tools to agents:

### `activate_sop(sop_name)`

Activate a SOP and load its full instructions. This makes the SOP the active one and loads its tools if available.

```python
# Agent calls this when a SOP is relevant
result = await activate_sop(ctx, "arxiv-search")
```

### `read_sop_resource(sop_name, resource_name)`

Read additional resource files (FORMS.md, REFERENCE.md, etc.).

```python
result = await read_sop_resource(ctx, "pdf-processing", "FORMS.md")
```

## Dynamic Toolsets

SOPs can provide their own tools by including a `tools/toolset.py` file:

```python
# tools/toolset.py
from pydantic_ai.toolsets import FunctionToolset

sop_ts = FunctionToolset(id="my-sop-tools")

@sop_ts.tool
async def my_custom_tool(ctx, param: str) -> str:
    """A custom tool for this SOP."""
    return f"Processed: {param}"
```

When `activate_sop` is called, the toolset is dynamically loaded and its tools become available to the agent.

## System Prompt

The `get_sops_system_prompt()` method generates a system prompt that:

- Lists all available SOPs with descriptions
- Explains SOP states and activation rules
- Provides usage instructions

**Important:** Add this to your agent's system prompt to enable proper SOP discovery and usage.

## API Reference

### SOPsToolset

```python
class SOPsToolset(FunctionToolset):
    def __init__(
        self,
        directories: list[str | Path],
        *,
        auto_discover: bool = True,
        validate: bool = True,
        toolset_id: str = 'sops',
    ): ...

    def get_sops_system_prompt(self) -> str: ...
    def get_sop(self, name: str) -> SOP: ...
    def refresh(self) -> None: ...

    @property
    def sops(self) -> dict[str, SOP]: ...
```

### SOP

```python
@dataclass
class SOP:
    name: str
    path: Path
    metadata: SOPMetadata
    content: str
    has_toolset: bool
    resources: list[SOPResource]
```

## Security

- Only use SOPs from trusted sources
- SOPs can provide instructions and code to agents
- Malicious SOPs could direct agents to perform unintended actions
- Audit SOPs from untrusted sources before use

## Related Resources

- [Pydantic AI Documentation](https://ai.pydantic.dev/)

## License

MIT License - see [LICENSE](LICENSE) file for details.