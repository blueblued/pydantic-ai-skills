# Technical Specification: Anthropic Agent Skills for Pydantic AI

**Version:** 1.0
**Status:** Draft
**Last Updated:** December 2025
**Author:** Douglas Trajano and Perplexity.AI

---

## 1. Overview

**pydantic-ai-skills** is a Python package that provides a standardized, composable framework for building and managing Agent Skills within the Pydantic AI ecosystem. Agent Skills are modular collections of instructions, scripts, tools, and resources that enable AI agents to progressively discover, load, and execute specialized capabilities for domain-specific tasks.

This package implements Anthropic's Agent Skills framework as a first-class citizen in Pydantic AI, bridging the gap between modular skill design and Pydantic AI's agent orchestration capabilities. The package enables developers to:

- **Define skills** using a declarative, filesystem-based structure
- **Discover and load skills** dynamically at runtime (tool-calling)
- **Integrate skills** seamlessly with Pydantic AI agents
- **Share and reuse skills** across projects and teams
- **Manage skill metadata** and versioning

### Key Objectives

- Provide a production-ready, extensible agent skills framework for Pydantic AI
- Standardize skill structure and metadata formats
- Enable seamless integration with Pydantic AI agents
- Support progressive disclosure of skill information
- Facilitate skill discovery, validation, and lifecycle management

---

## 2. Problem Context

### Technical Challenges

**Fragmented Agent Development:** Current approaches to building specialized AI agents often result in hardcoded, monolithic implementations that are difficult to reuse, test, and maintain across different projects and teams.

**Limited Tool Composability:** While Pydantic AI supports tool integration, there is no standardized way to package, version, and discover collections of related tools (skills) that serve a specific domain.

**Knowledge Integration Complexity:** Agents struggle with efficiently loading and managing domain-specific knowledge. Loading all information upfront creates latency and token waste; loading information on-demand requires complex orchestration logic.

**Skill Discoverability:** Developers lack a standard mechanism to discover available skills, understand their capabilities, assess compatibility, and manage dependencies between skills.

**Maintenance and Sharing:** Sharing agent capabilities across teams and projects requires manual reimplementation or ad-hoc packaging, increasing technical debt and reducing consistency.

### Background

Anthropic introduced Agent Skills as a conceptual framework emphasizing progressive disclosure—the principle of loading information only when needed. However, Python tooling and framework support for implementing this pattern within Pydantic AI remains underdeveloped.

Pydantic AI provides a flexible foundation for agent orchestration and tool integration but does not natively support the skill abstraction layer. This gap creates friction for teams adopting Anthropic's Agent Skills design principles.

### Constraints

- **Python 3.10+:** Must support modern Python versions with type hints
- **Pydantic AI API:** Must work seamlessly with current and near-future versions of Pydantic AI
- **Performance:** Skill loading and discovery must have minimal latency overhead
- **Lightweight:** Should not introduce heavy dependencies or bloat the agent runtime
- **Backward Compatibility:** Must maintain stability across minor version updates

---

## 3. Goals and Non-Goals

### Goals

✅ **Provide a standardized skill package structure** that defines how skills are organized, documented, and distributed
✅ **Enable dynamic skill discovery and loading** at runtime with automatic metadata extraction
✅ **Integrate seamlessly with Pydantic AI agents** to register tools and system prompts
✅ **Support progressive disclosure patterns** for efficient knowledge management
✅ **Implement skill versioning and dependency resolution** for compatibility management
✅ **Provide a skill validation framework** to ensure correctness before runtime
✅ **Support both local and remote skill sources** (filesystem, HTTP, package index)
✅ **Enable skill composition** so agents can load multiple skills in a coordinated manner
✅ **Implement comprehensive logging and observability** for debugging and monitoring
✅ **Provide clear documentation and examples** for skill developers and consumers

### Non-Goals

❌ Build a centralized skill marketplace or registry (though architecture should support it)
❌ Implement multi-agent orchestration workflows (Pydantic AI handles this)
❌ Create LLM-agnostic tool calling (use Pydantic AI's existing implementations)
❌ Provide GUI/web interface for skill management
❌ Implement advanced permission/RBAC systems beyond basic skill isolation
❌ Support non-Python skill implementations in this initial release
❌ Replace Pydantic AI's existing tool infrastructure (augment, not replace)

---

## 4. Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Pydantic AI Agent                         │
├─────────────────────────────────────────────────────────────┤
│  Skills Directory (Orchestration & Dependency Resolution)   │
├─────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │  Skill A   │  │  Skill B   │  │  Skill C   │  ...        │
│  │ (Tools +   │  │ (Tools +   │  │ (Tools +   │             │
│  │  Context)  │  │  Context)  │  │  Context)  │             │
│  └────────────┘  └────────────┘  └────────────┘             │
├─────────────────────────────────────────────────────────────┤
│  Skill Discovery & Loading (Local / Remote Sources)         │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │Filesystem│  │  HTTP    │  │ Registry │  ...             │
│  │Source    │  │ Source   │  │ Source   │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Skill Definition & Structure**

   - Filesystem-based skill packages with standardized directory layout
   - Markdown-based documentation with YAML frontmatter (`SKILL.md` is required; `FORMS.md`, `REFERENCE.md` are optional)
   - Optional Python scripts in `scripts/` directory (for script-based skills)
   - Three main skill patterns:
     - **Script-based**: Executable Python scripts with command-line interfaces (e.g., arxiv-search)
     - **Process-oriented**: Workflow instructions using existing agent tools (e.g., web-research)
     - **Tool-integration**: Domain-specific guidance for existing tools (e.g., langgraph-docs)

2. **SkillsToolset**

   - Pydantic AI toolset for skill discovery and management
   - Automatically discovers and validates skills from directories
   - Provides four tools to agents:
     - `list_skills()`: List available skills
     - `load_skill(name)`: Load skill instructions
     - `read_skill_resource(skill_name, resource_name)`: Read additional resources
     - `run_skill_script(skill_name, script_name, args)`: Execute scripts
   - Generates system prompt with skill usage instructions

3. **Skill Discovery & Loading**

   - Filesystem-based skill discovery
   - Validates skill structure and metadata on load
   - Parses YAML frontmatter from SKILL.md
   - Indexes available scripts and resources

4. **Progressive Disclosure**

   - Skills are loaded progressively through tool calls
   - Agents discover skills via `list_skills()`
   - Agents load instructions only when needed via `load_skill()`
   - Agents access detailed resources only when required via `read_skill_resource()`

5. **Validation & Safety**

   - Skill schema validation against defined specifications
   - YAML frontmatter parsing and validation
   - Security checks (safe script paths, path traversal prevention)

6. **Observability & Monitoring**
   - Structured logging for skill lifecycle events (discovery, loading, execution)
   - Performance metrics for skill operations

---

## 5. Detailed Design

### 5.1 Skill Directory Structure

A skill is packaged as a standardized directory with the following structure:

**Minimal Structure** (required):

```
my-skill/
└── SKILL.md                      # Main instructions and skill metadata
```

**Basic Structure** (common):

```
my-skill/
├── SKILL.md                      # Main instructions and skill metadata
└── scripts/
    └── my_tool.py                # Tool implementation (if needed)
```

**Extended Structure** (optional):

For more complex skills requiring additional documentation and resources:

```
my-skill/
├── SKILL.md                      # Main instructions and skill metadata
├── FORMS.md                      # Form-filling guide and templates (optional)
├── REFERENCE.md                  # Detailed API reference and documentation (optional)
├── EDGE_CASES.md                 # Edge case handling guide (optional)
├── TROUBLESHOOTING.md            # Troubleshooting guide (optional)
├── scripts/
│   ├── __init__.py
│   ├── primary_tool.py           # Primary tool implementations
│   ├── secondary_tool.py
│   └── utilities.py              # Helper functions
├── examples/
│   ├── basic_usage.py
│   ├── advanced_usage.py
│   └── integration_test.py
└── resources/
    ├── templates/
    ├── data/
    └── external_apis.json        # API configurations
```

### 5.2 Skill Metadata Format (SKILL.md)

The `SKILL.md` file serves as the main entry point for a skill, containing both metadata (in YAML frontmatter) and instructions in Markdown format.

**Required frontmatter fields:**

- `name`: The skill identifier
- `description`: Brief description of what the skill does

**Optional frontmatter fields:**
You can add any additional fields you need for your own tracking and organization, such as `version`, `author`, `category`, `tags`, etc.

**Example 1: Process-oriented skill (web-research)**

```markdown
---
name: web-research
description: Use this skill for requests related to web research; it provides a structured approach to conducting comprehensive web research
---

# Web Research Skill

This skill provides a structured approach to conducting comprehensive web research using the `task` tool to spawn research subagents. It emphasizes planning, efficient delegation, and systematic synthesis of findings.

## When to Use This Skill

Use this skill when you need to:
- Research complex topics requiring multiple information sources
- Gather and synthesize current information from the web
- Conduct comparative analysis across multiple subjects
- Produce well-sourced research reports with clear citations

## Research Process

### Step 1: Create and Save Research Plan

Before delegating to subagents, you MUST:

1. **Create a research folder** - Organize all research files in a dedicated folder:
   ```
   mkdir research_[topic_name]
   ```

2. **Analyze the research question** - Break it down into distinct, non-overlapping subtopics

3. **Write a research plan file** - Use the `write_file` tool to create `research_[topic_name]/research_plan.md`

### Step 2: Delegate to Research Subagents

For each subtopic in your plan:

1. **Use the `task` tool** to spawn a research subagent with:
   - Clear, specific research question
   - Instructions to write findings to a file
   - Budget: 3-5 web searches maximum

### Step 3: Synthesize Findings

After all subagents complete:

1. **Review the findings files** that were saved locally
2. **Synthesize the information** - Create a comprehensive response
3. **Write final report** (optional)

## Best Practices

- **Plan before delegating** - Always write research_plan.md first
- **Clear subtopics** - Ensure each subagent has distinct, non-overlapping scope
- **File-based communication** - Have subagents save findings to files
```

**Example 2: Script-based skill (arxiv-search)**

```markdown
---
name: arxiv-search
description: Search arXiv preprint repository for papers in physics, mathematics, computer science, quantitative biology, and related fields
---

# arXiv Search Skill

This skill provides access to arXiv, a free distribution service and open-access archive for scholarly articles.

## When to Use This Skill

Use this skill when you need to:
- Find preprints and recent research papers before journal publication
- Search for papers in computational biology, bioinformatics, or systems biology
- Access mathematical or statistical methods papers relevant to biology
- Find machine learning papers applied to biological problems

## How to Use

The skill provides a Python script that searches arXiv and returns formatted results.

### Basic Usage

**Note:** Always use the absolute path from your skills directory.

```bash
python3 [YOUR_SKILLS_DIR]/arxiv-search/arxiv_search.py "your search query" [--max-papers N]
```

**Arguments:**
- `query` (required): The search query string
- `--max-papers` (optional): Maximum number of papers to retrieve (default: 10)

### Examples

```bash
python3 ~/.skills/arxiv-search/arxiv_search.py "deep learning drug discovery" --max-papers 5
```

## Output Format

The script returns formatted results with:
- **Title**: Paper title
- **Summary**: Abstract/summary text

## Dependencies

This skill requires the `arxiv` Python package. If missing:

```bash
python3 -m pip install arxiv
```
```

**Example 3: Tool-integration skill (langgraph-docs)**

```markdown
---
name: langgraph-docs
description: Use this skill for requests related to LangGraph in order to fetch relevant documentation to provide accurate, up-to-date guidance.
---

# langgraph-docs

## Overview

This skill explains how to access LangGraph Python documentation to help answer questions and guide implementation.

## Instructions

### 1. Fetch the Documentation Index

Use the fetch_url tool to read the following URL:
https://docs.langchain.com/llms.txt

This provides a structured list of all available documentation with descriptions.

### 2. Select Relevant Documentation

Based on the question, identify 2-4 most relevant documentation URLs from the index. Prioritize:
- Specific how-to guides for implementation questions
- Core concept pages for understanding questions
- Tutorials for end-to-end examples
- Reference docs for API details

### 3. Fetch Selected Documentation

Use the fetch_url tool to read the selected documentation URLs.

### 4. Provide Accurate Guidance

After reading the documentation, complete the users request.
```

**Example script implementation (arxiv_search.py):**

```python
#!/usr/bin/env python3
"""arXiv Search.

Searches the arXiv preprint repository for research papers.
"""

import argparse


def query_arxiv(query: str, max_papers: int = 10) -> str:
    """Query arXiv for papers based on the provided search query.

    Parameters
    ----------
    query : str
        The search query string.
    max_papers : int
        The maximum number of papers to retrieve (default: 10).

    Returns
    -------
    str
        The formatted search results or an error message.
    """
    try:
        import arxiv
    except ImportError:
        return "Error: arxiv package not installed. Install with: pip install arxiv"

    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=query, max_results=max_papers, sort_by=arxiv.SortCriterion.Relevance
        )
        results = "\n\n".join(
            [f"Title: {paper.title}\nSummary: {paper.summary}" for paper in client.results(search)]
        )
        return results if results else "No papers found on arXiv."
    except Exception as e:
        return f"Error querying arXiv: {e}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Search arXiv for research papers")
    parser.add_argument("query", type=str, help="Search query string")
    parser.add_argument(
        "--max-papers",
        type=int,
        default=10,
        help="Maximum number of papers to retrieve (default: 10)",
    )

    args = parser.parse_args()

    print(query_arxiv(args.query, max_papers=args.max_papers))


if __name__ == "__main__":
    main()
```

### 5.3 Forms and Templates (FORMS.md)

**Note:** The `FORMS.md` file is optional and only needed for skills that involve structured data input or complex parameter configurations. Most simple skills (like the examples above) do not require this file.

The `FORMS.md` file contains form-filling guides and templates for skills with complex input requirements:

```markdown
# Document Processing Forms

## Extraction Request Form

Use this form when requesting document extraction:

| Field          | Type    | Required | Description                        |
| -------------- | ------- | -------- | ---------------------------------- |
| file_path      | string  | Yes      | Full path to the document          |
| format         | enum    | Yes      | One of: pdf, docx, txt             |
| extract_images | boolean | No       | Whether to extract embedded images |
| ocr_enabled    | boolean | No       | Enable OCR for scanned documents   |

## Batch Processing Form

For processing multiple documents:

| Field         | Type    | Required | Description                        |
| ------------- | ------- | -------- | ---------------------------------- |
| directory     | string  | Yes      | Directory containing documents     |
| recursive     | boolean | No       | Process subdirectories             |
| output_format | enum    | No       | Output format: json, csv, markdown |
```

### 5.4 API Reference (REFERENCE.md)

**Note:** The `REFERENCE.md` file is optional and only needed for skills with complex APIs, detailed data models, or extensive error handling. Simple skills typically include all necessary documentation in SKILL.md.

The `REFERENCE.md` file contains detailed API documentation for complex skills:

```markdown
# Document Processing API Reference

## Data Models

### ExtractionResult

| Property                       | Type         | Description                    |
| ------------------------------ | ------------ | ------------------------------ |
| text                           | string       | Extracted text content         |
| metadata                       | object       | Extraction metadata            |
| metadata.page_count            | integer      | Number of pages processed      |
| metadata.extraction_confidence | number (0-1) | Confidence score               |
| structured_data                | array        | Structured data elements found |

### StructureAnalysis

| Property      | Type   | Description                  |
| ------------- | ------ | ---------------------------- |
| document_type | string | Detected document type       |
| sections      | array  | List of document sections    |
| hierarchy     | object | Document structure hierarchy |

## Error Codes

| Code    | Description        |
| ------- | ------------------ |
| DOC_001 | File not found     |
| DOC_002 | Unsupported format |
| DOC_003 | Extraction failed  |
| DOC_004 | OCR not available  |
```

### 5.5 Progressive Disclosure with Skills Tools

Skills are discovered and loaded progressively through the SkillsToolset tools:

1. **list_skills()**: Agents first discover available skills with their names and descriptions
2. **load_skill(name)**: Agents load the main instructions for a specific skill when needed
3. **read_skill_resource(skill_name, resource_name)**: Agents load additional resources (FORMS.md, REFERENCE.md) only when required
4. **run_skill_script(skill_name, script_name, args)**: Agents execute skill scripts with arguments

This approach implements progressive disclosure—loading information only when needed, reducing token usage and improving response time.

### 5.6 Skills Integration with Pydantic AI

The package provides a simple, ergonomic API for integrating skills with Pydantic AI agents through the `SkillsToolset` class:

```python
from pydantic_ai import Agent
from pydantic_ai_skills.toolset import SkillsToolset

# Initialize Skills Toolset with one or more skill directories
skills_toolset = SkillsToolset(
    directories=["./skills"]  # Can include multiple directories
)

# Create agent with skills as a toolset
agent = Agent(
    model='openai:gpt-4o',
    instructions="You are a helpful research assistant.",
    toolsets=[skills_toolset]  # Skills tools automatically registered
)

# Add skills system prompt to agent
@agent.system_prompt
def add_skills_to_system_prompt() -> str:
    return skills_toolset.get_skills_system_prompt()

# Use agent - skills tools are available for the agent to call
result = await agent.run(
    "What are the last 3 papers on arXiv about machine learning?"
)
print(result.output)
```

**How it works:**

1. **Initialization**: SkillsToolset discovers all skills in the specified directories
2. **Registration**: Four tools are automatically registered with the agent:
   - `list_skills()`: Discover available skills
   - `load_skill(name)`: Load a skill's instructions
   - `read_skill_resource(skill_name, resource_name)`: Read skill resources
   - `run_skill_script(skill_name, script_name, args)`: Execute skill scripts
3. **System Prompt**: The system prompt guides the agent on when and how to use these tools and skills
4. **Progressive Loading**: The agent calls tools to load only the information needed

**Key Design Principles:**

1. **Tool-Based**: Skills are accessed through tools, enabling progressive disclosure
2. **Simple Integration**: Registered as a Pydantic AI toolset following framework patterns
3. **Zero Configuration**: No manual tool registration required
4. **Multiple Directories**: Support for skills from multiple sources

## 6. Data Models and Schemas

### 6.1 Core Data Models

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass
class SkillMetadata:
    """Skill metadata from SKILL.md frontmatter.

    Only `name` and `description` are required. Other fields
    (version, author, category, tags, etc.) can be added dynamically
    based on frontmatter content.
    """
    name: str
    description: str
    # Optional fields can be added dynamically as attributes
    # Examples: version, author, category, tags, dependencies, etc.

@dataclass
class SkillResource:
    """A resource file within a skill (e.g., FORMS.md, REFERENCE.md)."""
    name: str  # Resource filename (e.g., "FORMS.md")
    path: Path  # Absolute path to the resource file
    content: str | None = None  # Loaded content (lazy-loaded)

@dataclass
class SkillScript:
    """An executable script within a skill.

    Script-based tools: Executable Python scripts in scripts/ directory.
    Can be executed via SkillsToolset.run_skill_script() tool.
    """
    name: str  # Script name without .py extension
    path: Path  # Absolute path to the script file
    skill_name: str  # Parent skill name

@dataclass
class Skill:
    """A loaded skill instance."""
    name: str  # Skill name (from metadata)
    path: Path  # Absolute path to skill directory
    metadata: SkillMetadata  # Parsed metadata from SKILL.md
    content: str  # Main content from SKILL.md (without frontmatter)
    resources: list[SkillResource]  # Optional resource files (FORMS.md, etc.)
    scripts: list[SkillScript]  # Available scripts in scripts/ directory
```

## 7. APIs and Interfaces

### 7.1 SkillsToolset API

```python
from pathlib import Path

class SkillsToolset:
    """Pydantic AI toolset for automatic skill discovery and integration.

    This is the primary interface for integrating skills with Pydantic AI agents.
    It implements the toolset protocol and automatically discovers, loads, and
    registers skills from specified directories.

    Provides the following tools to agents:
    - list_skills(): List all available skills
    - load_skill(name): Load a specific skill's instructions
    - read_skill_resource(skill_name, resource_name): Read a skill resource file
    - run_skill_script(skill_name, script_name, args): Execute a skill script
    """

    def __init__(
        self,
        directories: list[str | Path],
        auto_discover: bool = True,
        validate: bool = True,
    ) -> None:
        """Initialize the skills toolset.

        Args:
            directories: List of directory paths to search for skills
            auto_discover: Automatically discover and load skills on init
            validate: Validate skill structure and metadata on load
        """
        ...

    def get_skills_system_prompt(self) -> str:
        """Get the combined system prompt from all loaded skills.

        This should be added to the agent's system prompt to provide
        skill discovery and usage instructions.

        Returns:
            Formatted system prompt containing skill discovery instructions
        """
        ...

    # Tools available to agents (registered automatically)

    def list_skills(self) -> str:
        """List all available skills with their descriptions.

        This tool is automatically registered with the agent and can be called
        to discover available skills.

        Returns:
            Formatted list of skills with names and descriptions
        """
        ...

    def load_skill(self, name: str) -> str:
        """Load a specific skill's main instructions.

        This tool loads the main SKILL.md content (without frontmatter) for
        a specific skill, enabling progressive disclosure.

        Args:
            name: The skill name to load

        Returns:
            The skill's main instructions content
        """
        ...

    def read_skill_resource(self, skill_name: str, resource_name: str) -> str:
        """Read a skill resource file (e.g., FORMS.md, REFERENCE.md).

        This tool loads additional resource files for a skill, supporting
        progressive disclosure of detailed information.

        Args:
            skill_name: The skill name
            resource_name: The resource filename (e.g., "FORMS.md")

        Returns:
            The resource file content
        """
        ...

    def run_skill_script(
        self,
        skill_name: str,
        script_name: str,
        args: list[str] | None = None
    ) -> str:
        """Execute a skill script with arguments.

        This tool runs a Python script from a skill's scripts/ directory,
        passing the provided arguments.

        Args:
            skill_name: The skill name
            script_name: The script name (without .py extension)
            args: Optional list of command-line arguments

        Returns:
            The script's output (stdout)
        """
        ...
```

## 8. Technology Stack

| Component              | Technology                 | Rationale                                                       |
| ---------------------- | -------------------------- | --------------------------------------------------------------- |
| **Language**           | Python 3.10+               | Primary language for AI agent development; strong async support |
| **Agent Framework**    | Pydantic AI                | Primary integration target; tight coupling by design            |
| **Type System**        | Python builtin dataclasses | Data validation, serialization, schema generation               |
| **Async Runtime**      | asyncio                    | Python standard; native support in Pydantic AI                  |
| **Configuration**      | PyYAML                     | Standard for configuration files; human-readable                |
| **Validation**         | jsonschema                 | JSON Schema validation for skill metadata                       |
| **Logging**            | Python logging   | Structured logging for observability ("pydantic-ai-skills" logger)        |
| **Package Management** | uv                         | Lightweight package management and distribution                 |
| **Testing**            | pytest + pytest-asyncio    | Async testing support                                           |

## 11. Error Handling and Observability

### 11.1 Error Handling Strategy

```python
class SkillException(Exception):
    """Base exception for skill-related errors."""
    pass

class SkillNotFoundError(SkillException):
    """Skill not found in any source."""
    pass

class SkillValidationError(SkillException):
    """Skill validation failed."""
    pass

class SkillResourceLoadError(SkillException):
    """Failed to load skill resources."""
    pass

class SkillScriptExecutionError(SkillException):
    """Skill script execution failed."""
    pass
```

## 12. Assumptions and Constraints

### Assumptions

1. **Skill developers follow standards:** Developers will adhere to the skill package structure and metadata format
2. **Pydantic AI stability:** Pydantic AI API is stable; only minor breaking changes expected
3. **Python environment:** Agents run in controlled Python environments with package management
4. **Single-machine deployment (initially):** Multi-machine deployment handled at application layer
5. **Skill script idempotency:** Skill scripts are idempotent or side-effects are acceptable
6. **Documentation stability:** Skill documentation changes are backward-compatible or versioned
7. **User expertise:** Skill developers understand Python, async patterns, and Pydantic AI

### Constraints

- **Python 3.10+ only:** Cannot support older Python versions due to typing requirements
- **Filesystem permissions:** Permission to read skill directories and execute scripts through Python subprocess
- **LLM token budget:** Progressive disclosure necessary to avoid token explosion
- **Async first design:** All I/O operations must be async-compatible

---

## 14. Implementation Plan

### Phase 1: Foundation (Weeks 1-3)

**Objectives:** Build core infrastructure and tool integration

- [ ] Design and implement core data models: `Skill`, `SkillMetadata`, `SkillResource`, `SkillScript`
- [ ] Implement skill discovery from filesystem directories
- [ ] Create YAML frontmatter parser for SKILL.md files
- [ ] Build `SkillsToolset` class with four core tools:
  - [ ] `list_skills()` - List available skills
  - [ ] `load_skill(name)` - Load skill instructions
  - [ ] `read_skill_resource(skill_name, resource_name)` - Read resources
  - [ ] `run_skill_script(skill_name, script_name, args)` - Execute scripts
- [ ] Implement skill validation framework
- [ ] Write unit tests (target: 80% coverage)
- [ ] Create example skills (arxiv-search, web-research, langgraph-docs)
- [ ] Create initial documentation

**Deliverables:**

- Core library with SkillsToolset
- Three example skills demonstrating all patterns
- README and quickstart guide

### Phase 2: Optimization & Production Readiness (Weeks 4-6)

**Objectives:** Performance, security, and production readiness

- [ ] Add async file operations for skill loading
- [ ] Implement security checks (path traversal prevention, safe script execution)
- [ ] Add structured logging for all operations
- [ ] Performance benchmarking and profiling
- [ ] Load testing with 50+ skills
- [ ] Error handling and recovery mechanisms
- [ ] Integration tests for multi-skill scenarios

**Deliverables:**

- Production-ready library
- Performance benchmarks
- Security audit report

### Phase 3: Documentation & Release (Weeks 7-8)

**Objectives:** Production release

- [ ] Comprehensive API documentation
- [ ] Skill developer guide with examples
- [ ] Best practices guide
- [ ] PyPI packaging and release
- [ ] Community feedback incorporation

**Deliverables:**

- v1.0.0 release on PyPI
- Complete documentation
- Example skills repository
- Developer onboarding guide

### Milestones

| Milestone        | Target Date | Status  |
| ---------------- | ----------- | ------- |
| Phase 1 Complete | Week 3      | Pending |
| Phase 2 Complete | Week 6      | Pending |
| v1.0.0 Release   | Week 8      | Pending |

---

## 15. Open Questions

1. **Script Execution Security:** Should we sandbox script execution or rely on Python subprocess isolation?

2. **Resource Caching:** Should resources (FORMS.md, REFERENCE.md) be cached in memory after first load, or always read from disk?

3. **Skill Validation Strictness:** Should we fail on missing optional resources, or only warn?

4. **Script Output Format:** Should we enforce JSON output from scripts, or support any text output?

5. **Multiple Directories Priority:** When the same skill exists in multiple directories, which one takes precedence?

6. **System Prompt Length:** Should we limit the system prompt length to avoid token overhead?

---

## 16. Risks and Mitigations

| Risk                                         | Severity | Likelihood | Mitigation                                                                           |
| -------------------------------------------- | -------- | ---------- | ------------------------------------------------------------------------------------ |
| **Pydantic AI API instability**              | High     | Medium     | Version pinning; adapter pattern for API changes; close monitoring of Pydantic AI   |
| **Performance degradation with many skills** | Medium   | Medium     | Load testing at scale; lazy loading; profiling and optimization                     |
| **Security vulnerabilities in scripts**      | High     | Medium     | Script execution isolation; path validation; security audit; code review process    |
| **Poor adoption due to learning curve**      | Medium   | Medium     | Comprehensive documentation; interactive examples; skill templates                  |
| **Token cost from system prompts**           | Medium   | High       | Progressive disclosure via tools; concise system prompts; skill summary only        |
| **Script execution errors**                  | Medium   | High       | Robust error handling; clear error messages; validation before execution            |

---

## 17. Alternatives Considered

### Alternative 1: Preload All Skills into System Prompt

**Approach:** Load all skill instructions into the system prompt at initialization.

**Pros:**
- Simple implementation
- No tool calls needed for skill access
- Lower latency for skill usage

**Cons:**
- Token cost explosion with many skills
- No progressive disclosure
- **Decision: Rejected** — Violates core progressive disclosure principle

### Alternative 2: Class-Based Skills (Inheritance Model)

**Approach:** Skills as Python classes that inherit from a base `Skill` class.

**Pros:**
- Familiar OOP pattern
- Type safety with inheritance
- IDE autocomplete support

**Cons:**
- Tight coupling to Python
- Harder to share and distribute
- More complex for skill developers
- **Decision: Rejected** — Filesystem-based approach is simpler and more accessible

### Alternative 3: Single Skill Loading Tool

**Approach:** One tool that loads everything about a skill at once.

**Pros:**
- Simpler API (fewer tools)
- Fewer tool calls

**Cons:**
- No progressive disclosure of resources
- Higher token cost per skill load
- **Decision: Rejected** — Separate tools enable finer-grained progressive disclosure
- **Decision: Rejected** — Multiple loader sources provide flexibility; federation model better for enterprise

### Alternative 4: Skill Validation at Load Time Only

**Approach:** Validate skills only when loading, not at definition time.

**Pros:**

- Simpler API
- Faster development cycle

**Cons:**

- Runtime failures harder to diagnose
- Poor developer experience
- **Decision: Rejected** — Early validation catches issues faster and improves quality

---

## 18. Appendix: Example Usage

### Example 1: Basic Agent with Skills

```python
from pydantic_ai import Agent
from pydantic_ai_skills.toolset import SkillsToolset

# Initialize Skills Toolset
skills_toolset = SkillsToolset(
    directories=["./skills"]
)

# Create agent with skills
agent = Agent(
    model='openai:gpt-4o',
    instructions="You are a helpful research assistant.",
    toolsets=[skills_toolset]
)

# Add skills system prompt
@agent.system_prompt
def add_skills_to_system_prompt() -> str:
    return skills_toolset.get_skills_system_prompt()

# Use agent - it will discover and use skills as needed
result = await agent.run(
    "Search arXiv for papers on transformer architectures"
)
print(result.output)
```

### Example 2: Agent Tool Usage Flow

The agent will automatically use the skills tools:

```python
# Agent internally makes tool calls like:
# 1. list_skills() -> Discovers arxiv-search skill
# 2. load_skill("arxiv-search") -> Loads instructions
# 3. run_skill_script("arxiv-search", "arxiv_search", ["transformer", "--max-papers", "5"])
```

### Example 3: Creating a Custom Skill

Create a new skill directory with SKILL.md:

```markdown
---
name: weather-lookup
description: Get weather information for any location
---

# Weather Lookup Skill

Use this skill to get current weather information.

## When to Use This Skill

Use when the user asks about:
- Current weather conditions
- Temperature for a location
- Weather forecasts

## How to Use

This skill provides a Python script for fetching weather data.

```bash
python3 [YOUR_SKILLS_DIR]/weather-lookup/weather.py <city>
```

### Example

```bash
python3 ~/.skills/weather-lookup/weather.py "San Francisco"
```
```

Create the corresponding script in `scripts/weather.py`:

```python
#!/usr/bin/env python3
"""Weather lookup script."""
import sys

def get_weather(city: str) -> str:
    # Implementation here
    return f"Weather data for {city}"

if __name__ == "__main__":
    city = sys.argv[1]
    print(get_weather(city))
```

---

## Appendix A: Skill Design Patterns (from Examples)

Based on analysis of example skills in the `examples/skills/` directory, three core design patterns have emerged:

### Pattern 1: Script-Based Skills (arxiv-search)

**Characteristics:**
- Provides standalone Python script(s) in `scripts/` directory
- Scripts have command-line interfaces with argparse
- Skills document how to execute scripts with arguments
- Agents invoke via subprocess or similar execution methods

**When to use:**
- Skill requires external library dependencies (e.g., `arxiv` package)
- Logic is complex enough to warrant separate, testable implementation
- Script can be used independently outside agent context
- Need to encapsulate implementation details from agent

**Example structure:**
```
arxiv-search/
├── SKILL.md              # Usage instructions and examples
└── arxiv_search.py       # Standalone executable script
```

### Pattern 2: Process-Oriented Skills (web-research)

**Characteristics:**
- No custom code - purely instructional content
- Provides step-by-step workflows and best practices
- Guides agents on how to orchestrate existing tools effectively
- Emphasizes planning, delegation, and synthesis patterns

**When to use:**
- Skill represents a methodology or workflow rather than a tool
- Implementation uses existing agent capabilities (task spawning, file I/O)
- Focus is on coordination and process rather than new functionality
- Want to encode domain expertise and best practices

**Example structure:**
```
web-research/
└── SKILL.md              # Workflow instructions and best practices
```

### Pattern 3: Tool-Integration Skills (langgraph-docs)

**Characteristics:**
- Minimal instructions focused on effective tool usage
- Guides agents to use existing tools (e.g., `fetch_url`) for specific domains
- Provides context like URLs, query patterns, or data sources
- No custom implementation - enhances existing capabilities

**When to use:**
- Skill adds domain knowledge to existing tools
- Success depends on knowing where/how to fetch information
- Want to standardize approach to a common information source
- Tool capability exists but needs domain-specific guidance

**Example structure:**
```
langgraph-docs/
└── SKILL.md              # Tool usage instructions with domain context
```

### Key Design Principles from Examples

1. **Simplicity First**: Start with minimal SKILL.md; add FORMS.md/REFERENCE.md only when complexity demands it
2. **Clear "When to Use"**: All examples include explicit guidance on when the skill is appropriate
3. **Practical Examples**: Concrete usage examples with actual commands/workflows
4. **Dependency Transparency**: Clear documentation of external dependencies and installation instructions
5. **Process Documentation**: Process-oriented skills document best practices and common pitfalls

### Choosing the Right Pattern

**Decision tree:**

```
Does the skill need custom code?
├─ Yes → Does it have external dependencies or complex logic?
│         ├─ Yes → Use Script-Based pattern (Pattern 1)
│         └─ No → Consider inline tool definition
└─ No → Does it represent a workflow/methodology?
          ├─ Yes → Use Process-Oriented pattern (Pattern 2)
          └─ No → Use Tool-Integration pattern (Pattern 3)
```
