# SkillsToolset API Reference

::: pydantic_ai_skills.toolset.SkillsToolset
options:
members: - **init** - get_skills_system_prompt - get_skill - refresh - skills
show_source: true
heading_level: 2

## Helper Functions

::: pydantic_ai_skills.toolset.discover_skills
options:
show_source: true
heading_level: 3

::: pydantic_ai_skills.toolset.parse_skill_md
options:
show_source: true
heading_level: 3

## Usage Examples

### Initialize Toolset

```python
from pydantic_ai_skills import SkillsToolset

# Basic initialization
toolset = SkillsToolset(directories=["./skills"])

# Advanced initialization
toolset = SkillsToolset(
    directories=["./skills", "./shared"],
    auto_discover=True,
    validate=True,
    toolset_id="my-skills",
    script_timeout=60
)
```

### Get Skills System Prompt

```python
from pydantic_ai import Agent
from pydantic_ai_skills import SkillsToolset

toolset = SkillsToolset(directories=["./skills"])

agent = Agent(
    model='openai:gpt-4o',
    toolsets=[toolset]
)

@agent.system_prompt
async def add_skills():
    return toolset.get_skills_system_prompt()
```

**Important**: The system prompt function can be either synchronous or asynchronous as current Pydantic AI implementation.

**What the system prompt contains**:

- List of all available skills with their names and descriptions
- Instructions on how to use the four skill tools (`load_skill`, `read_skill_resource`, `run_skill_script`, `list_skills`)
- Best practices for progressive disclosure (load only what's needed when needed)

This enables the agent to discover and select skills without calling `list_skills()` first, following Anthropic's approach to skill exposure.

### Access Skills

```python
# Get all skills
all_skills = toolset.skills

# Get specific skill
skill = toolset.get_skill("arxiv-search")

print(f"Name: {skill.name}")
print(f"Description: {skill.metadata.description}")
print(f"Scripts: {[s.name for s in skill.scripts]}")
```

### Refresh Skills

```python
# Initial load
toolset = SkillsToolset(directories=["./skills"])
print(f"Loaded {len(toolset.skills)} skills")

# ... Add or modify skills in ./skills/ ...

# Reload skills
toolset.refresh()
print(f"Now have {len(toolset.skills)} skills")
```

### Discover Skills Manually

```python
from pydantic_ai_skills import discover_skills

skills = discover_skills(
    directories=["./skills"],
    validate=True
)

for skill in skills:
    print(f"{skill.name}: {skill.metadata.description}")
```

### Parse SKILL.md

```python
from pydantic_ai_skills import parse_skill_md

content = """---
name: my-skill
description: My skill description
version: 1.0.0
---

# My Skill

Instructions go here...
"""

frontmatter, instructions = parse_skill_md(content)

print(f"Name: {frontmatter['name']}")
print(f"Description: {frontmatter['description']}")
print(f"Version: {frontmatter['version']}")
print(f"Instructions: {instructions}")
```

## Tools Provided

The `SkillsToolset` automatically registers four tools with agents:

### list_skills()

Lists all available skills with descriptions.

**Returns**: Formatted markdown string

**Example**:

```markdown
# Available Skills

## arxiv-search

Search arXiv for research papers (scripts: arxiv_search)

## web-research

Structured approach to web research
```

### load_skill(skill_name: str)

Loads full instructions for a specific skill.

**Parameters**:

- `skill_name` (str): Name of the skill to load

**Returns**: Full skill content including metadata and instructions

### read_skill_resource(skill_name: str, resource_name: str)

Reads a resource file from a skill.

**Parameters**:

- `skill_name` (str): Name of the skill
- `resource_name` (str): Resource filename (e.g., "REFERENCE.md")

**Returns**: Resource file content

### run_skill_script(skill_name: str, script_name: str, args: list[str] | None = None)

Executes a skill script.

**Parameters**:

- `skill_name` (str): Name of the skill
- `script_name` (str): Script name without .py extension
- `args` (list[str], optional): Command-line arguments

**Returns**: Script output (stdout and stderr)

**Raises**:

- `SkillScriptExecutionError`: If script execution fails or times out

## See Also

- [Types Reference](types.md) - Type definitions
- [Exceptions Reference](exceptions.md) - Exception classes
- [Creating Skills](../creating-skills.md) - How to create skills
