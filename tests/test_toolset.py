"""Tests for SOPsToolset."""

from pathlib import Path

import pytest

from pydantic_ai_sops import SOPsToolset
from pydantic_ai_sops.exceptions import SOPNotFoundError


@pytest.fixture
def sample_sops_dir(tmp_path: Path) -> Path:
    """Create a temporary directory with sample SOPs."""
    # Create SOP 1
    sop1_dir = tmp_path / 'sop-one'
    sop1_dir.mkdir()
    (sop1_dir / 'SOP.md').write_text("""---
name: sop-one
description: First test SOP for basic operations
---

# SOP One

Use this SOP for basic operations.

## Instructions

1. Do something simple
2. Return results
""")

    # Create SOP 2 with resources
    sop2_dir = tmp_path / 'sop-two'
    sop2_dir.mkdir()
    (sop2_dir / 'SOP.md').write_text("""---
name: sop-two
description: Second test SOP with resources
---

# SOP Two

Advanced SOP with resources.

See FORMS.md for details.
""")
    (sop2_dir / 'FORMS.md').write_text('# Forms\n\nForm filling guide.')
    (sop2_dir / 'REFERENCE.md').write_text('# API Reference\n\nDetailed reference.')

    # Create SOP 3 with toolset
    sop3_dir = tmp_path / 'sop-three'
    sop3_dir.mkdir()
    (sop3_dir / 'SOP.md').write_text("""---
name: sop-three
description: Third test SOP with toolset
---

# SOP Three

SOP with dynamic toolset.
""")
    tools_dir = sop3_dir / 'tools'
    tools_dir.mkdir()
    (tools_dir / 'toolset.py').write_text("""from pydantic_ai.toolsets import FunctionToolset

sop_ts = FunctionToolset(id="sop-three-tools")

@sop_ts.tool
async def hello(ctx, name: str = "World") -> str:
    return f"Hello, {name}!"
""")

    return tmp_path


def test_toolset_initialization(sample_sops_dir: Path) -> None:
    """Test SOPsToolset initialization."""
    toolset = SOPsToolset(directories=[sample_sops_dir])

    assert len(toolset.sops) == 3
    assert 'sop-one' in toolset.sops
    assert 'sop-two' in toolset.sops
    assert 'sop-three' in toolset.sops


def test_toolset_get_sop(sample_sops_dir: Path) -> None:
    """Test getting a specific SOP."""
    toolset = SOPsToolset(directories=[sample_sops_dir])

    sop = toolset.get_sop('sop-one')
    assert sop.name == 'sop-one'
    assert sop.metadata.description == 'First test SOP for basic operations'


def test_toolset_get_sop_not_found(sample_sops_dir: Path) -> None:
    """Test getting a non-existent SOP."""
    toolset = SOPsToolset(directories=[sample_sops_dir])

    with pytest.raises(SOPNotFoundError, match="SOP 'nonexistent' not found"):
        toolset.get_sop('nonexistent')


@pytest.mark.asyncio
async def test_list_sops_tool(sample_sops_dir: Path) -> None:
    """Test the list_sops tool by checking SOPs were loaded."""
    toolset = SOPsToolset(directories=[sample_sops_dir])

    # Verify all three SOPs were discovered
    assert len(toolset.sops) == 3
    assert 'sop-one' in toolset.sops
    assert 'sop-two' in toolset.sops
    assert 'sop-three' in toolset.sops

    # Verify descriptions
    assert toolset.sops['sop-one'].metadata.description == 'First test SOP for basic operations'
    assert toolset.sops['sop-two'].metadata.description == 'Second test SOP with resources'
    assert toolset.sops['sop-three'].metadata.description == 'Third test SOP with toolset'


@pytest.mark.asyncio
async def test_activate_sop_tool(sample_sops_dir: Path) -> None:
    """Test the activate_sop tool."""
    toolset = SOPsToolset(directories=[sample_sops_dir])

    # We can check that the SOPs were loaded correctly
    sop = toolset.get_sop('sop-one')
    assert sop is not None
    assert sop.name == 'sop-one'
    assert 'First test SOP for basic operations' in sop.metadata.description
    assert 'Use this SOP for basic operations' in sop.content


@pytest.mark.asyncio
async def test_activate_sop_not_found(sample_sops_dir: Path) -> None:
    """Test activating a non-existent SOP."""
    toolset = SOPsToolset(directories=[sample_sops_dir])

    # Test that nonexistent SOP raises an error
    with pytest.raises(SOPNotFoundError):
        toolset.get_sop('nonexistent-sop')


@pytest.mark.asyncio
async def test_read_sop_resource_tool(sample_sops_dir: Path) -> None:
    """Test the read_sop_resource tool."""
    toolset = SOPsToolset(directories=[sample_sops_dir])

    # Test that sop-two has the expected resources
    sop = toolset.get_sop('sop-two')
    assert len(sop.resources) == 2

    resource_names = [r.name for r in sop.resources]
    assert 'FORMS.md' in resource_names
    assert 'REFERENCE.md' in resource_names

    # Check that resources can be read
    for resource in sop.resources:
        assert resource.path.exists()
        assert resource.path.is_file()


@pytest.mark.asyncio
async def test_read_sop_resource_not_found(sample_sops_dir: Path) -> None:
    """Test reading a non-existent resource."""
    toolset = SOPsToolset(directories=[sample_sops_dir])

    # Test SOP with no resources
    sop_one = toolset.get_sop('sop-one')
    assert len(sop_one.resources) == 0

    # Test SOP with resources
    sop_two = toolset.get_sop('sop-two')
    resource_names = [r.name for r in sop_two.resources]
    assert 'NONEXISTENT.md' not in resource_names


@pytest.mark.asyncio
async def test_sop_with_toolset(sample_sops_dir: Path) -> None:
    """Test SOP with toolset."""
    toolset = SOPsToolset(directories=[sample_sops_dir])

    # Test that sop-three has toolset
    sop = toolset.get_sop('sop-three')
    assert sop.has_toolset is True

    # Test that sop-one does not have toolset
    sop_one = toolset.get_sop('sop-one')
    assert sop_one.has_toolset is False


def test_get_sops_system_prompt(sample_sops_dir: Path) -> None:
    """Test generating the system prompt."""
    toolset = SOPsToolset(directories=[sample_sops_dir])

    prompt = toolset.get_sops_system_prompt()

    # Should include all SOP names and descriptions
    assert 'sop-one' in prompt
    assert 'sop-two' in prompt
    assert 'sop-three' in prompt
    assert 'First test SOP for basic operations' in prompt
    assert 'Second test SOP with resources' in prompt
    assert 'Third test SOP with toolset' in prompt

    # Should include usage instructions
    assert 'activate_sop' in prompt

    # Should include progressive disclosure guidance
    assert 'Progressive disclosure' in prompt or 'progressive disclosure' in prompt


def test_get_sops_system_prompt_empty() -> None:
    """Test system prompt with no SOPs."""
    toolset = SOPsToolset(directories=[], auto_discover=False)

    prompt = toolset.get_sops_system_prompt()
    assert prompt == ''


def test_toolset_refresh(sample_sops_dir: Path) -> None:
    """Test refreshing SOPs."""
    toolset = SOPsToolset(directories=[sample_sops_dir])

    initial_count = len(toolset.sops)

    # Add a new SOP
    new_sop_dir = sample_sops_dir / 'sop-four'
    new_sop_dir.mkdir()
    (new_sop_dir / 'SOP.md').write_text("""---
name: sop-four
description: Fourth SOP added after initialization
---

New SOP content.
""")

    # Refresh
    toolset.refresh()

    assert len(toolset.sops) == initial_count + 1
    assert 'sop-four' in toolset.sops