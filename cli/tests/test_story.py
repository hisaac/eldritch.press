"""Check story loading against temporary Markdown files and YAML metadata."""

from pathlib import Path

import pytest

from miskatron.story import Story


@pytest.fixture
def story_files(tmp_path: Path) -> tuple[Path, Path]:
	"""Create a fictional story and return its Markdown and metadata paths."""
	source_file = tmp_path / "the-sentient-teapot.md"
	source_file.write_text(
		"# The Sentient Teapot\n\nThe teapot demanded a tiny hat.\n", encoding="utf-8"
	)
	config_file = tmp_path / "book.yaml"
	config_file.write_text(
		"title: The Sentient Teapot\nauthor: Professor Wobble\npublished: 2042\n",
		encoding="utf-8",
	)
	return source_file, config_file


def test_loads_metadata(story_files: tuple[Path, Path]) -> None:
	"""Read the title, author, and publication year from the sidecar file."""
	story = Story.from_files(*story_files)

	assert story.title == "The Sentient Teapot"
	assert story.author == "Professor Wobble"
	assert story.published == 2042


def test_defaults_language_to_english(story_files: tuple[Path, Path]) -> None:
	"""Use English when the metadata omits the language field."""
	assert Story.from_files(*story_files).language == "en"


def test_preserves_explicit_language(story_files: tuple[Path, Path]) -> None:
	"""Keep the language supplied by the editor."""
	source_file, config_file = story_files
	with config_file.open("a", encoding="utf-8") as config:
		config.write("language: fr\n")

	assert Story.from_files(source_file, config_file).language == "fr"


def test_rejects_missing_title(story_files: tuple[Path, Path]) -> None:
	"""Report the missing title when the remaining metadata is valid."""
	source_file, config_file = story_files
	config_file.write_text(
		"author: Professor Wobble\npublished: 2042\n", encoding="utf-8"
	)

	with pytest.raises(ValueError, match="'title' must be a non-empty string"):
		Story.from_files(source_file, config_file)


@pytest.mark.parametrize("published", ['"2042"', "2042.5", "true", "null"])
def test_rejects_non_integer_year(
	story_files: tuple[Path, Path], published: str
) -> None:
	"""Reject quoted years, fractional years, booleans, and null."""
	source_file, config_file = story_files
	config_file.write_text(
		f"title: The Sentient Teapot\nauthor: Professor Wobble\npublished: {published}\n",
		encoding="utf-8",
	)

	with pytest.raises(ValueError, match="'published' must be an integer year"):
		Story.from_files(source_file, config_file)


def test_preserves_story_text(story_files: tuple[Path, Path]) -> None:
	"""Preserve Markdown markup, Unicode text, and trailing newlines when loading a story."""
	source_file, config_file = story_files
	text = "# The Sentient Teapot\n\n> Never trust a kettle in a waistcoat.\\\n> —Captain Noodle\n\n*Emphasis* and café…\n\n"
	source_file.write_text(text, encoding="utf-8")

	assert Story.from_files(source_file, config_file).text == text
