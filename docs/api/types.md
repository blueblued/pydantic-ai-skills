# Types API Reference

Type definitions for pydantic-ai-skills.

## Overview

The package uses dataclasses for type-safe skill representation:

- `Skill` - Complete skill with all components
- `SkillMetadata` - Skill metadata from YAML frontmatter
- `SkillResource` - Resource file within a skill
- `SkillScript` - Executable script within a skill

## Type Definitions

::: pydantic_ai_skills.types.Skill
    options:
      show_source: true
      heading_level: 3

::: pydantic_ai_skills.types.SkillMetadata
    options:
      show_source: true
      heading_level: 3

::: pydantic_ai_skills.types.SkillResource
    options:
      show_source: true
      heading_level: 3

::: pydantic_ai_skills.types.SkillScript
    options:
      show_source: true
      heading_level: 3

## Usage Examples

### SkillMetadata

```python
from pydantic_ai_skills import SkillMetadata

metadata = SkillMetadata(
    name="my-skill",
    description="Does something useful",
    extra={
        "version": "1.0.0",
        "author": "Your Name",
        "category": "utilities"
    }
)

print(metadata.name)  # "my-skill"
print(metadata.extra["version"])  # "1.0.0"
```

### Skill

```python
from pathlib import Path
from pydantic_ai_skills import Skill, SkillMetadata

skill = Skill(
    name="my-skill",
    path=Path("./skills/my-skill"),
    metadata=SkillMetadata(
        name="my-skill",
        description="My skill"
    ),
    content="# Instructions...",
    resources=[],
    scripts=[]
)

print(f"Name: {skill.name}")
print(f"Path: {skill.path}")
print(f"Has scripts: {len(skill.scripts) > 0}")
```

### SkillResource

```python
from pathlib import Path
from pydantic_ai_skills import SkillResource

resource = SkillResource(
    name="REFERENCE.md",
    path=Path("./skills/my-skill/REFERENCE.md"),
    content=None  # Lazy-loaded
)

# Load content when needed
if resource.path.exists():
    resource.content = resource.path.read_text()
```

### SkillScript

```python
from pathlib import Path
from pydantic_ai_skills import SkillScript

script = SkillScript(
    name="process_data",
    path=Path("./skills/my-skill/scripts/process_data.py"),
    skill_name="my-skill"
)

print(f"Script: {script.name}")
print(f"Belongs to: {script.skill_name}")
print(f"Location: {script.path}")
```

### Working with Skills

```python
from pydantic_ai_skills import SkillsToolset

toolset = SkillsToolset(directories=["./skills"])

# Access skills
for name, skill in toolset.skills.items():
    print(f"\nSkill: {name}")
    print(f"  Description: {skill.metadata.description}")
    print(f"  Path: {skill.path}")

    # Access metadata
    if "version" in skill.metadata.extra:
        print(f"  Version: {skill.metadata.extra['version']}")

    # List resources
    if skill.resources:
        print(f"  Resources:")
        for resource in skill.resources:
            print(f"    - {resource.name}")

    # List scripts
    if skill.scripts:
        print(f"  Scripts:")
        for script in skill.scripts:
            print(f"    - {script.name}")
```

## Type Relationships

```
Skill
├── name: str
├── path: Path
├── metadata: SkillMetadata
│   ├── name: str
│   ├── description: str
│   └── extra: dict[str, Any]
├── content: str
├── resources: list[SkillResource]
│   └── SkillResource
│       ├── name: str
│       ├── path: Path
│       └── content: str | None
└── scripts: list[SkillScript]
    └── SkillScript
        ├── name: str
        ├── path: Path
        └── skill_name: str
```

## See Also

- [SkillsToolset](toolset.md) - Main toolset API
- [Exceptions](exceptions.md) - Exception classes
- [Creating Skills](../creating-skills.md) - How to create skills
