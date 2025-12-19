"""Tests for pydantic-ai-skills types."""

from pathlib import Path

from pydantic_ai_skills.types import Skill, SkillMetadata, SkillResource, SkillScript


def test_skill_metadata_creation() -> None:
    """Test creating SkillMetadata with required fields."""
    metadata = SkillMetadata(name='test-skill', description='A test skill')

    assert metadata.name == 'test-skill'
    assert metadata.description == 'A test skill'
    assert metadata.extra == {}


def test_skill_metadata_with_extra_fields() -> None:
    """Test SkillMetadata with additional fields."""
    metadata = SkillMetadata(
        name='test-skill', description='A test skill', extra={'version': '1.0.0', 'author': 'Test Author'}
    )

    assert metadata.extra['version'] == '1.0.0'
    assert metadata.extra['author'] == 'Test Author'


def test_skill_resource_creation() -> None:
    """Test creating SkillResource."""
    resource = SkillResource(name='FORMS.md', path=Path('/tmp/skill/FORMS.md'))

    assert resource.name == 'FORMS.md'
    assert resource.path == Path('/tmp/skill/FORMS.md')
    assert resource.content is None


def test_skill_script_creation() -> None:
    """Test creating SkillScript."""
    script = SkillScript(name='test_script', path=Path('/tmp/skill/scripts/test_script.py'), skill_name='test-skill')

    assert script.name == 'test_script'
    assert script.path == Path('/tmp/skill/scripts/test_script.py')
    assert script.skill_name == 'test-skill'


def test_skill_creation() -> None:
    """Test creating a complete Skill."""
    metadata = SkillMetadata(name='test-skill', description='A test skill')
    resource = SkillResource(name='FORMS.md', path=Path('/tmp/skill/FORMS.md'))
    script = SkillScript(name='test_script', path=Path('/tmp/skill/scripts/test_script.py'), skill_name='test-skill')

    skill = Skill(
        name='test-skill',
        path=Path('/tmp/skill'),
        metadata=metadata,
        content='# Instructions\n\nTest instructions.',
        resources=[resource],
        scripts=[script],
    )

    assert skill.name == 'test-skill'
    assert skill.path == Path('/tmp/skill')
    assert skill.metadata.name == 'test-skill'
    assert skill.content == '# Instructions\n\nTest instructions.'
    assert len(skill.resources) == 1
    assert len(skill.scripts) == 1
