"""Tests for SOP discovery."""

from pathlib import Path

from pydantic_ai_sops.toolset import discover_sops


def test_discover_sops_single_sop(tmp_path: Path) -> None:
    """Test discovering a single SOP."""
    sop_dir = tmp_path / 'test-sop'
    sop_dir.mkdir()

    sop_md = sop_dir / 'SOP.md'
    sop_md.write_text("""---
name: test-sop
description: A test SOP
---

# Test SOP

Instructions here.
""")

    sops = discover_sops([tmp_path], validate=True)

    assert len(sops) == 1
    assert sops[0].name == 'test-sop'
    assert sops[0].description == 'A test SOP'
    assert 'Instructions here' in sops[0].content


def test_discover_sops_multiple_sops(tmp_path: Path) -> None:
    """Test discovering multiple SOPs."""
    # Create first skill
    sop1_dir = tmp_path / 'sop-one'
    sop1_dir.mkdir()
    (sop1_dir / 'SOP.md').write_text("""---
name: sop-one
description: First SOP
---

Content 1.
""")

    # Create second skill
    sop2_dir = tmp_path / 'sop-two'
    sop2_dir.mkdir()
    (sop2_dir / 'SOP.md').write_text("""---
name: sop-two
description: Second SOP
---

Content 2.
""")

    sops = discover_sops([tmp_path], validate=True)

    assert len(sops) == 2
    sop_names = {s.name for s in sops}
    assert sop_names == {'sop-one', 'sop-two'}


def test_discover_sops_with_resources(tmp_path: Path) -> None:
    """Test discovering skills with resource files."""
    sop_dir = tmp_path / 'test-sop'
    sop_dir.mkdir()

    (sop_dir / 'SOP.md').write_text("""---
name: test-sop
description: SOP with resources
---

See FORMS.md for details.
""")

    (sop_dir / 'FORMS.md').write_text('# Forms\n\nForm documentation.')
    (sop_dir / 'REFERENCE.md').write_text('# Reference\n\nAPI reference.')

    sops = discover_sops([tmp_path], validate=True)

    assert len(sops) == 1
    assert len(sops[0].resources) == 2
    resource_names = {r.name for r in sops[0].resources}
    assert resource_names == {'FORMS.md', 'REFERENCE.md'}


def test_discover_sops_with_scripts(tmp_path: Path) -> None:
    """Test discovering skills with scripts."""
    sop_dir = tmp_path / 'test-sop'
    sop_dir.mkdir()

    (sop_dir / 'SOP.md').write_text("""---
name: test-sop
description: SOP with scripts
---

Use the search script.
""")

    scripts_dir = sop_dir / 'scripts'
    scripts_dir.mkdir()
    (scripts_dir / 'search.py').write_text('#!/usr/bin/env python3\nprint("searching")')
    (scripts_dir / 'process.py').write_text('#!/usr/bin/env python3\nprint("processing")')

    sops = discover_sops([tmp_path], validate=True)

    assert len(sops) == 1
    assert len(sops[0].scripts) == 2
    script_names = {s.name for s in sops[0].scripts}
    assert script_names == {'search', 'process'}


def test_discover_sops_nested_directories(tmp_path: Path) -> None:
    """Test discovering skills in nested directories."""
    nested_dir = tmp_path / 'category' / 'subcategory' / 'test-sop'
    nested_dir.mkdir(parents=True)

    (nested_dir / 'SOP.md').write_text("""---
name: nested-sop
description: Nested SOP
---

Content.
""")

    sops = discover_sops([tmp_path], validate=True)

    assert len(sops) == 1
    assert sops[0].name == 'nested-sop'


def test_discover_sops_missing_name_with_validation(tmp_path: Path) -> None:
    """Test discovering skill missing name field with validation enabled."""
    sop_dir = tmp_path / 'test-sop'
    sop_dir.mkdir()

    (sop_dir / 'SOP.md').write_text("""---
description: Missing name field
---

Content.
""")

    # With validation, should skip this skill (log warning)
    sops = discover_sops([tmp_path], validate=True)
    assert len(sops) == 0


def test_discover_sops_missing_name_without_validation(tmp_path: Path) -> None:
    """Test discovering skill missing name field without validation."""
    sop_dir = tmp_path / 'test-sop'
    sop_dir.mkdir()

    (sop_dir / 'SOP.md').write_text("""---
description: Missing name field
---

Content.
""")

    # Without validation, uses folder name
    sops = discover_sops([tmp_path], validate=False)
    assert len(sops) == 1
    assert sops[0].name == 'test-sop'  # Uses folder name


def test_discover_sops_nonexistent_directory(tmp_path: Path) -> None:
    """Test discovering skills from non-existent directory."""
    nonexistent = tmp_path / 'does-not-exist'

    # Should not raise, just log warning
    sops = discover_sops([nonexistent], validate=True)
    assert len(sops) == 0


def test_discover_sops_resources_subdirectory(tmp_path: Path) -> None:
    """Test discovering resources in resources/ subdirectory."""
    sop_dir = tmp_path / 'test-sop'
    sop_dir.mkdir()

    (sop_dir / 'SOP.md').write_text("""---
name: test-sop
description: SOP with resources subdirectory
---

Content.
""")

    resources_dir = sop_dir / 'resources'
    resources_dir.mkdir()
    (resources_dir / 'schema.json').write_text('{}')
    (resources_dir / 'template.txt').write_text('template')

    nested_dir = resources_dir / 'nested'
    nested_dir.mkdir()
    (nested_dir / 'data.csv').write_text('col1,col2')

    sops = discover_sops([tmp_path], validate=True)

    assert len(sops) == 1
    assert len(sops[0].resources) == 3

    resource_names = {r.name for r in sops[0].resources}
    assert 'resources/schema.json' in resource_names
    assert 'resources/template.txt' in resource_names
    assert 'resources/nested/data.csv' in resource_names
