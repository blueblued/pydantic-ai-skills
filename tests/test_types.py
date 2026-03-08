"""Tests for pydantic-ai-sops types."""

from pathlib import Path

from pydantic_ai_sops.types import SOP, SOPMetadata, SOPResource


def test_sop_metadata_creation() -> None:
    """Test creating SOPMetadata with required fields."""
    metadata = SOPMetadata(name='test-sop', description='A test SOP')

    assert metadata.name == 'test-sop'
    assert metadata.description == 'A test SOP'
    assert metadata.extra == {}


def test_sop_metadata_with_extra_fields() -> None:
    """Test SOPMetadata with additional fields."""
    metadata = SOPMetadata(
        name='test-sop', description='A test SOP', extra={'version': '1.0.0', 'author': 'Test Author'}
    )

    assert metadata.extra['version'] == '1.0.0'
    assert metadata.extra['author'] == 'Test Author'


def test_sop_resource_creation() -> None:
    """Test creating SOPResource."""
    resource = SOPResource(name='FORMS.md', path=Path('/tmp/sop/FORMS.md'))

    assert resource.name == 'FORMS.md'
    assert resource.path == Path('/tmp/sop/FORMS.md')
    assert resource.content is None


def test_sop_creation() -> None:
    """Test creating a complete SOP."""
    metadata = SOPMetadata(name='test-sop', description='A test SOP')
    resource = SOPResource(name='FORMS.md', path=Path('/tmp/sop/FORMS.md'))

    sop = SOP(
        name='test-sop',
        path=Path('/tmp/sop'),
        metadata=metadata,
        content='# Instructions\n\nTest instructions.',
        resources=[resource],
    )

    assert sop.name == 'test-sop'
    assert sop.path == Path('/tmp/sop')
    assert sop.metadata.name == 'test-sop'
    assert sop.content == '# Instructions\n\nTest instructions.'
    assert len(sop.resources) == 1
    assert sop.has_toolset is False


def test_sop_with_toolset() -> None:
    """Test creating a SOP with toolset."""
    metadata = SOPMetadata(name='test-sop', description='A test SOP with toolset')

    sop = SOP(
        name='test-sop',
        path=Path('/tmp/sop'),
        metadata=metadata,
        content='# Instructions',
        has_toolset=True,
    )

    assert sop.has_toolset is True


def test_sop_description_property() -> None:
    """Test SOP description property."""
    metadata = SOPMetadata(name='test-sop', description='Test description')
    sop = SOP(
        name='test-sop',
        path=Path('/tmp/sop'),
        metadata=metadata,
        content='Content',
    )

    assert sop.description == 'Test description'