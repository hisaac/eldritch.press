"""Discover story folders and load the Markdown and metadata shared by every edition."""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Story:
	"""A story’s original Markdown and the publication metadata from its book.yaml."""

	title: str
	author: str
	published: int
	language: str
	text: str

	@classmethod
	def from_files(cls, source_file: Path, config_file: Path) -> Story:
		"""Read UTF-8 Markdown and validate its YAML metadata, defaulting a missing language to English."""

		text = source_file.read_text(encoding="utf-8")
		config = yaml.safe_load(config_file.read_text(encoding="utf-8"))

		if not isinstance(config, dict):
			raise TypeError(f"{config_file}: expected a YAML mapping")

		config.setdefault("language", "en")

		for field in ("title", "author", "language"):
			value = config.get(field)
			if not isinstance(value, str) or not value.strip():
				raise ValueError(f"{config_file}: '{field}' must be a non-empty string")

		# bool is a subclass of int in Python, so an exact type check rejects YAML true and false.
		if type(config.get("published")) is not int:
			raise ValueError(f"{config_file}: 'published' must be an integer year")

		return cls(
			title=config["title"],
			author=config["author"],
			published=config["published"],
			language=config["language"],
			text=text,
		)


def discover_stories(directory: Path) -> list[Path]:
	"""Return sorted story folders under directory, rejecting duplicate author/story output paths."""

	if not directory.is_dir():
		raise ValueError(f"Not a directory: {directory}")

	folders = sorted(
		book.parent for book in directory.resolve().rglob("book.yaml") if book.is_file()
	)
	if not folders:
		raise ValueError(f"No book.yaml files found in {directory}")

	# Only the final two directory names appear in the published URL.
	seen = {}
	for folder in folders:
		key = (folder.parent.name, folder.name)
		if key in seen:
			raise ValueError(f"Stories share an output path: {seen[key]} and {folder}")
		seen[key] = folder
	return folders


def load_story(story_dir: Path) -> Story:
	"""Load book.yaml and the Markdown file named after its enclosing story folder."""
	if not story_dir.is_dir():
		raise ValueError(f"Not a directory: {story_dir}")

	story_file = story_dir / f"{story_dir.name}.md"
	if not story_file.is_file():
		raise ValueError(f"Story file not found: {story_file}")

	config_file = story_dir / "book.yaml"
	if not config_file.is_file():
		raise ValueError(f"Book config file not found: {config_file}")

	return Story.from_files(story_file, config_file)
