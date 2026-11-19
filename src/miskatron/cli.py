import argparse
import shutil
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from miskatron.epub import build_epub
from miskatron.render import environment, format_publication_file, render_web_page
from miskatron.story import Story


def main() -> None:
	parser = argparse.ArgumentParser(prog="msk")
	commands = parser.add_subparsers(dest="command", required=True)

	build_parser = commands.add_parser(
		"build", help="Build stories found recursively under a directory"
	)
	build_parser.add_argument(
		"directory", type=Path, nargs="?", default=Path("stories")
	)
	build_parser.add_argument("--format", choices=("html", "epub"), default="html")

	commands.add_parser("dist", help="Build the complete distribution site")
	args = parser.parse_args()
	try:
		if args.command == "dist":
			build_all(Path("dist"))
		else:
			folders = discover_stories(args.directory)
			if args.format == "epub":
				for folder in folders:
					print(f"Wrote {build_epub(load_story(folder), folder)}")
			else:
				build_site(folders, Path("build"))
	except (OSError, ValueError, TypeError, yaml.YAMLError) as error:
		parser.error(str(error))


def discover_stories(directory: Path) -> list[Path]:
	if not directory.is_dir():
		raise ValueError(f"Not a directory: {directory}")
	folders = sorted(
		book.parent for book in directory.resolve().rglob("book.yaml") if book.is_file()
	)
	if not folders:
		raise ValueError(f"No book.yaml files found in {directory}")
	seen = {}
	for folder in folders:
		key = (folder.parent.name, folder.name)
		if key in seen:
			raise ValueError(f"Stories share an output path: {seen[key]} and {folder}")
		seen[key] = folder
	return folders


def build_all(output: Path = Path("build")) -> None:
	build_site(discover_stories(Path("stories")), output)


def build_site(folders: list[Path], output: Path) -> None:
	if any(folder.is_relative_to(output.resolve()) for folder in folders):
		raise ValueError(
			f"Story sources must be outside the output directory: {output}"
		)
	with TemporaryDirectory(dir=output.parent) as tmp:
		site = Path(tmp) / "site"
		site.mkdir()
		assemble_site(site, folders, include_unpacked=output == Path("build"))
		previous = Path(tmp) / "previous"
		if output.exists():
			output.rename(previous)
		try:
			site.rename(output)
		except OSError:
			if previous.exists():
				previous.rename(output)
			raise
	print(f"Wrote {output / 'index.html'}")


def assemble_site(site: Path, folders: list[Path], *, include_unpacked: bool) -> None:
	entries = []
	for folder in folders:
		story, page = build_story(
			folder, site, unpack_root=site if include_unpacked else None
		)
		href = page.relative_to(site)
		entries.append(
			(story, href.as_posix(), href.parent.with_suffix(".epub").as_posix())
		)
	entries.sort(key=lambda entry: entry[0].title.casefold())
	template = environment.get_template("index.html")
	html = format_publication_file(template.render(entries=entries), "index.html")
	index = site / "index.html"
	index.parent.mkdir(exist_ok=True)
	write_stylesheet(index.parent)
	index.write_text(html, encoding="utf-8")


def load_story(story_dir: Path) -> Story:

	if not story_dir.is_dir():
		raise ValueError(f"Not a directory: {story_dir}")

	story_file = story_dir / f"{story_dir.name}.md"
	if not story_file.is_file():
		raise ValueError(f"Story file not found: {story_file}")

	config_file = story_dir / "book.yaml"
	if not config_file.is_file():
		raise ValueError(f"Book config file not found: {config_file}")

	return Story.from_files(story_file, config_file)


def build_story(
	story_dir: Path,
	site: Path = Path("dist"),
	*,
	unpack_root: Path | None = Path("build"),
) -> tuple[Story, Path]:
	story = load_story(story_dir)

	print(f"Loaded {story.title} by {story.author} ({story.published})")
	print(f"Language: {story.language}")
	print(f"Text length: {len(story.text)} characters")

	cover = story_dir / "cover.png"
	archive = build_epub(story, story_dir, site, unpack_root=unpack_root)
	html = render_web_page(
		story, has_cover=cover.is_file(), epub_href=f"../{archive.name}"
	)

	output_dir = site / story_dir.parent.name / story_dir.name
	output_dir.mkdir(parents=True, exist_ok=True)

	write_stylesheet(output_dir)
	if cover.is_file():
		shutil.copyfile(cover, output_dir / "cover.png")
	else:
		(output_dir / "cover.png").unlink(missing_ok=True)

	output_file = output_dir / "index.html"
	output_file.write_text(html, encoding="utf-8")

	return story, output_file


def write_stylesheet(output_dir: Path) -> None:
	stylesheet = files("miskatron").joinpath("styles", "story.css")
	css = format_publication_file(stylesheet.read_text(encoding="utf-8"), "story.css")
	(output_dir / "story.css").write_text(css, encoding="utf-8")
