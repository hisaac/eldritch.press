from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class Story:
	title: str
	author: str
	published: int
	language: str
	text: str

	@classmethod
	def from_files(cls, source_file: Path, config_file: Path) -> Story:
		text = source_file.read_text(encoding="utf-8")
		config = yaml.safe_load(config_file.read_text(encoding="utf-8"))

		if not isinstance(config, dict):
			raise TypeError(f"{config_file}: expected a YAML mapping")

		config.setdefault("language", "en")

		for field in ("title", "author", "language"):
			value = config.get(field)
			if not isinstance(value, str) or not value.strip():
				raise ValueError(f"{config_file}: '{field}' must be a non-empty string")

		if type(config.get("published")) is not int:
			raise ValueError(f"{config_file}: 'published' must be an integer year")

		return cls(
			title=config["title"],
			author=config["author"],
			published=config["published"],
			language=config["language"],
			text=text,
		)
