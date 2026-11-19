import argparse
from importlib.resources import files
from pathlib import Path

import yaml

from miskatron.render import format_publication_file, render_web_page
from miskatron.story import Story


def main() -> None:
	parser = argparse.ArgumentParser(prog="misk")
	commands = parser.add_subparsers(dest="command", required=True)

	build_parser = commands.add_parser("build", help="Build a store EPUB")
	build_parser.add_argument("story_dir", type=Path)

	args = parser.parse_args()

	story_dir = args.story_dir.resolve()

	if not story_dir.is_dir():
		parser.error(f"Not a directory: {story_dir}")

	story_file = story_dir / f"{story_dir.name}.md"
	if not story_file.is_file():
		parser.error(f"Story file not found: {story_file}")

	config_file = story_dir / "book.yaml"
	if not story_file.is_file():
		parser.error(f"Book config file not found: {config_file}")

	try:
		story = Story.from_files(story_file, config_file)
	except (OSError, ValueError, TypeError, yaml.YAMLError) as error:
		parser.error(str(error))

	print(f"Loaded {story.title} by {story.author} ({story.published})")
	print(f"Language: {story.language}")
	print(f"Text length: {len(story.text)} characters")

	html = render_web_page(story)

	output_dir = Path("generated") / story_dir.parent.name / story_dir.name
	output_dir.mkdir(parents=True, exist_ok=True)

	stylesheet = files("miskatron").joinpath("styles", "story.css")
	css = format_publication_file(stylesheet.read_text(encoding="utf-8"), "story.css")
	(output_dir / "story.css").write_text(css, encoding="utf-8")

	output_file = output_dir / "index.html"
	output_file.write_text(html, encoding="utf-8")

	print(f"Wrote {output_file}")
