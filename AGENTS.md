# Copilot Instructions for pydantic-ai-skills

## Project Overview

This is a Python library implementing [Anthropic's Agent Skills framework](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) for Pydantic AI. Skills are modular collections of instructions, scripts, and resources that extend AI agent capabilities through progressive disclosure (load-on-demand to reduce token usage).

## Architecture

**Core Components** in [pydantic_ai_skills/](pydantic_ai_skills/):

- [toolset.py](pydantic_ai_skills/toolset.py): `SkillsToolset` extends Pydantic AI's `FunctionToolset`, auto-registers 4 tools: `list_skills`, `load_skill`, `read_skill_resource`, `run_skill_script`
- [types.py](pydantic_ai_skills/types.py): Dataclass definitions (`Skill`, `SkillMetadata`, `SkillResource`, `SkillScript`)
- [exceptions.py](pydantic_ai_skills/exceptions.py): Hierarchy with base `SkillException` and specific subclasses

**Skill Structure** (filesystem-based):

```markdown
skill-name/
├── SKILL.md          # Required: YAML frontmatter + markdown instructions
├── FORMS.md          # Optional: form-filling guides
├── REFERENCE.md      # Optional: API reference
└── scripts/          # Optional: executable Python scripts
    └── script_name.py
```

## Code Conventions

**Naming (Anthropic conventions enforced via validation warnings):**

- Skill names: lowercase, hyphens only (e.g., `arxiv-search`, `web-research`)
- Pattern: `^[a-z0-9-]+$`, max 64 chars
- Avoid reserved words: `anthropic`, `claude`

**Style:**

- Single quotes for strings (configured in `ruff`)
- Google docstring convention
- Type hints required (Python 3.10+)
- Line length: 120 chars

**Tool Registration Pattern** (see [toolset.py#L410-L450](pydantic_ai_skills/toolset.py#L410-L450)):

```python
@self.tool
async def tool_name(ctx: RunContext[Any], param: str) -> str:
    """Docstring becomes tool description for the LLM."""
    _ = ctx  # Required by Pydantic AI toolset protocol
    # implementation
```

## Development Commands

```bash
# Install with test dependencies
pip install -e ".[test]"

# Run tests with coverage (asyncio_mode=auto configured)
pytest

# Run specific test file
pytest tests/test_toolset.py -v

# Lint and format
ruff check pydantic_ai_skills/
ruff format pydantic_ai_skills/

# Build docs locally
pip install -e ".[docs]"
mkdocs serve
```

## Testing Patterns

Tests use `pytest` with `pytest-asyncio` (auto mode - no `@pytest.mark.asyncio` needed):

- Create temp skill directories via `tmp_path` fixture
- Test SKILL.md parsing with various frontmatter scenarios
- Script execution tests mock subprocess calls

Example fixture pattern from [test_toolset.py](tests/test_toolset.py):

```python
@pytest.fixture
def sample_skills_dir(tmp_path: Path) -> Path:
    skill_dir = tmp_path / 'skill-name'
    skill_dir.mkdir()
    (skill_dir / 'SKILL.md').write_text("""---
name: skill-name
description: Test skill
---
# Instructions here
""")
    return tmp_path
```

## Key Implementation Details

**YAML Frontmatter Parsing** ([toolset.py#L94-L121](pydantic_ai_skills/toolset.py#L94-L121)):

- Uses `yaml.safe_load` via PyYAML
- Pattern: `^---\s*\n(.*?)^---\s*\n` with DOTALL|MULTILINE
- Raises `SkillValidationError` on parse failure

**Security:**

- Path traversal prevention via `_is_safe_path()` before any file read
- Script timeout configurable (default 30s) via `script_timeout` param
- Uses `anyio.run_process` for async script execution

**Progressive Disclosure Flow:**

1. Agent receives skill list via `get_skills_system_prompt()`
2. Agent calls `load_skill(name)` to get full instructions
3. Optionally calls `read_skill_resource()` for additional docs
4. Executes `run_skill_script()` with args when needed

## Creating New Skills

Reference examples in [examples/skills/](examples/skills/). Minimum viable skill:

```markdown
---
name: my-skill
description: Brief description (max 1024 chars)
---

# Instructions

When to use, how to use, example invocations...
```

For skills with scripts, document args in SKILL.md and place Python files in `scripts/` subdirectory.
