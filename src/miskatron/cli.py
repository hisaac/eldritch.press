import argparse
import shutil
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml

from miskatron.epub import build_epub
from miskatron.pdf import PAPER_SIZES, pdf_name, write_pdfs, write_print_sources
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
	build_parser.add_argument(
		"--format", choices=("html", "epub", "pdf"), default="html"
	)

	build_parser.add_argument(
		"--paper",
		type=str.upper,
		choices=PAPER_SIZES,
		help="Paper size for --format pdf (default: both)",
	)

	commands.add_parser("dist", help="Build the complete distribution site")
	args = parser.parse_args()
	try:
		if args.command == "dist":
			build_all(Path("dist"))
		else:
			if args.paper and args.format != "pdf":
				parser.error("--paper requires --format pdf")
			folders = discover_stories(args.directory)
			if args.format == "epub":
				for folder in folders:
					print(f"Wrote {build_epub(load_story(folder), folder)}")
			elif args.format == "pdf":
				for folder in folders:
					write_pdfs(
						load_story(folder),
						Path("dist") / folder.parent.name / folder.name / "print",
						folder.name,
						(args.paper,) if args.paper else PAPER_SIZES,
					)
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
		assemble_site(site, folders, sources_only=output == Path("build"))
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


def assemble_site(site: Path, folders: list[Path], *, sources_only: bool) -> None:
	entries = []
	for folder in folders:
		story, page = build_story(folder, site, sources_only=sources_only)
		href = page.relative_to(site)
		downloads = href.parent.parent
		if sources_only:
			downloads = Path("../dist") / downloads
		entries.append(
			(
				story,
				href.as_posix(),
				(downloads / "ebook" / f"{folder.name}.epub").as_posix(),
				[
					(
						paper,
						(downloads / "print" / pdf_name(folder.name, paper)).as_posix(),
					)
					for paper in PAPER_SIZES
				],
			)
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
	sources_only: bool = False,
) -> tuple[Story, Path]:
	story = load_story(story_dir)

	print(f"Loaded {story.title} by {story.author} ({story.published})")
	print(f"Language: {story.language}")
	print(f"Text length: {len(story.text)} characters")

	root = site / story_dir.parent.name / story_dir.name
	if sources_only:
		with TemporaryDirectory() as tmp:
			build_epub(story, story_dir, Path(tmp), unpack_root=site)
		write_print_sources(story, root / "print", PAPER_SIZES)
	else:
		build_epub(story, story_dir, site, unpack_root=None)
		write_pdfs(story, root / "print", story_dir.name, PAPER_SIZES)
	download_root = Path("..")
	if sources_only:
		download_root = (
			Path("../../../../dist") / story_dir.parent.name / story_dir.name
		)
	page = write_story_page(story, story_dir, root / "web", download_root=download_root)
	return story, page


def write_story_page(
	story: Story, story_dir: Path, output_dir: Path, *, download_root: Path
) -> Path:
	cover = story_dir / "cover.png"
	html = render_web_page(
		story,
		has_cover=cover.is_file(),
		epub_href=(download_root / "ebook" / f"{story_dir.name}.epub").as_posix(),
		pdf_links=[
			(
				paper,
				(download_root / "print" / pdf_name(story_dir.name, paper)).as_posix(),
			)
			for paper in PAPER_SIZES
		],
	)
	output_dir.mkdir(parents=True, exist_ok=True)

	write_stylesheet(output_dir)
	if cover.is_file():
		shutil.copyfile(cover, output_dir / "cover.png")
	else:
		(output_dir / "cover.png").unlink(missing_ok=True)

	output_file = output_dir / "index.html"
	output_file.write_text(html, encoding="utf-8")

	return output_file


def write_stylesheet(output_dir: Path) -> None:
	stylesheet = files("miskatron").joinpath("styles", "story.css")
	css = format_publication_file(stylesheet.read_text(encoding="utf-8"), "story.css")
	(output_dir / "story.css").write_text(css, encoding="utf-8")
