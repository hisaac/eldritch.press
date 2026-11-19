import argparse
from importlib.resources import files
from pathlib import Path

import yaml

from miskatron.render import environment, format_publication_file, render_web_page
from miskatron.story import Story


def main() -> None:
	parser = argparse.ArgumentParser(prog="msk")
	commands = parser.add_subparsers(dest="command", required=True)

	build_parser = commands.add_parser("build", help="Build one story")
	build_parser.add_argument("story_dir", type=Path)

	commands.add_parser("build-all", help="Build all stories and their index")
	args = parser.parse_args()
	try:
		if args.command == "build-all":
			build_all()
		else:
			build_story(args.story_dir.resolve())
	except (OSError, ValueError, TypeError, yaml.YAMLError) as error:
		parser.error(str(error))


def build_all() -> None:
	entries = []
	for book in sorted(Path("stories").glob("*/*/book.yaml")):
		story, page = build_story(book.parent)
		entries.append((story, page.relative_to("generated").as_posix()))
	entries.sort(key=lambda entry: entry[0].title.casefold())
	template = environment.get_template("index.html")
	html = format_publication_file(template.render(entries=entries), "index.html")
	index = Path("generated/index.html")
	index.parent.mkdir(exist_ok=True)
	write_stylesheet(index.parent)
	index.write_text(html, encoding="utf-8")
	print(f"Wrote {index}")


def build_story(story_dir: Path) -> tuple[Story, Path]:

	if not story_dir.is_dir():
		raise ValueError(f"Not a directory: {story_dir}")

	story_file = story_dir / f"{story_dir.name}.md"
	if not story_file.is_file():
		raise ValueError(f"Story file not found: {story_file}")

	config_file = story_dir / "book.yaml"
	if not config_file.is_file():
		raise ValueError(f"Book config file not found: {config_file}")

	story = Story.from_files(story_file, config_file)

	print(f"Loaded {story.title} by {story.author} ({story.published})")
	print(f"Language: {story.language}")
	print(f"Text length: {len(story.text)} characters")

	html = render_web_page(story)

	output_dir = Path("generated") / story_dir.parent.name / story_dir.name
	output_dir.mkdir(parents=True, exist_ok=True)

	write_stylesheet(output_dir)

	output_file = output_dir / "index.html"
	output_file.write_text(html, encoding="utf-8")

	print(f"Wrote {output_file}")
	return story, output_file


def write_stylesheet(output_dir: Path) -> None:
	stylesheet = files("miskatron").joinpath("styles", "story.css")
	css = format_publication_file(stylesheet.read_text(encoding="utf-8"), "story.css")
	(output_dir / "story.css").write_text(css, encoding="utf-8")
