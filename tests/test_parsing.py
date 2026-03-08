"""Tests for SOP.md parsing."""

import pytest

from pydantic_ai_sops.exceptions import SOPValidationError
from pydantic_ai_sops.toolset import parse_sop_md


def test_parse_sop_md_with_frontmatter() -> None:
    """Test parsing SOP.md with valid frontmatter."""
    content = """---
name: test-sop
description: A test SOP for testing
version: 1.0.0
---

# Test SOP

This is the main content.
"""

    frontmatter, instructions = parse_sop_md(content)

    assert frontmatter['name'] == 'test-sop'
    assert frontmatter['description'] == 'A test SOP for testing'
    assert frontmatter['version'] == '1.0.0'
    assert instructions.startswith('# Test SOP')


def test_parse_sop_md_without_frontmatter() -> None:
    """Test parsing SOP.md without frontmatter."""
    content = """# Test SOP

This SOP has no frontmatter.
"""

    frontmatter, instructions = parse_sop_md(content)

    assert frontmatter == {}
    assert instructions.startswith('# Test SOP')


def test_parse_sop_md_empty_frontmatter() -> None:
    """Test parsing SOP.md with empty frontmatter."""
    content = """---
---

# Test SOP

Content here.
"""

    frontmatter, instructions = parse_sop_md(content)

    assert frontmatter == {}
    assert instructions.startswith('# Test SOP')


def test_parse_sop_md_invalid_yaml() -> None:
    """Test parsing SOP.md with invalid YAML."""
    content = """---
name: test-sop
description: [unclosed array
---

Content.
"""

    with pytest.raises(SOPValidationError, match='Failed to parse YAML frontmatter'):
        parse_sop_md(content)


def test_parse_sop_md_multiline_description() -> None:
    """Test parsing SOP.md with multiline description."""
    content = """---
name: test-sop
description: |
  This is a multiline
  description for testing
---

# Content
"""

    frontmatter, _ = parse_sop_md(content)

    assert 'multiline' in frontmatter['description']
    assert 'description for testing' in frontmatter['description']


def test_parse_sop_md_complex_frontmatter() -> None:
    """Test parsing SOP.md with complex frontmatter."""
    content = """---
name: complex-sop
description: Complex SOP with metadata
version: 2.0.0
author: Test Author
tags:
  - testing
  - example
metadata:
  category: test
  priority: high
---

# Complex SOP
"""

    frontmatter, _ = parse_sop_md(content)

    assert frontmatter['name'] == 'complex-sop'
    assert frontmatter['tags'] == ['testing', 'example']
    assert frontmatter['metadata']['category'] == 'test'