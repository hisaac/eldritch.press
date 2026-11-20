"""Coordinate the catalog and its editions, from story discovery to replacing the output tree."""

from pathlib import Path
from tempfile import TemporaryDirectory

from miskatron import story as stories
from miskatron.formats import epub, pdf, web
from miskatron.story import Story


def build_distribution() -> None:
	"""Build the complete website and its downloadable editions in .dist/."""
	folders = stories.discover_stories(Path("stories/source"))
	build_site(folders, Path(".dist"), sources_only=False)


def build_site(folders: list[Path], output: Path, *, sources_only: bool) -> None:
	"""Assemble the selected stories in a temporary directory, then replace the output tree."""

	if any(folder.is_relative_to(output.resolve()) for folder in folders):
		raise ValueError(
			f"Story sources must be outside the output directory: {output}"
		)

	with TemporaryDirectory() as tmp:
		site = Path(tmp) / "site"
		site.mkdir()
		assemble_site(site, folders, sources_only=sources_only)

		# Keep the previous site available to restore if the final move fails.
		output.parent.mkdir(parents=True, exist_ok=True)
		previous = Path(tmp) / "previous"
		if output.exists():
			output.move(previous)
		try:
			site.move(output)
		except OSError:
			if previous.exists():
				previous.move(output)
			raise
	print(f"Wrote {output / 'index.html'}")


def assemble_site(site: Path, folders: list[Path], *, sources_only: bool) -> None:
	"""Write the shared stylesheet, build each story, and link its browser page from the catalog."""
	stylesheet = web.write_stylesheet(site)
	entries = []
	for folder in folders:
		story, page = build_story(
			folder, site, sources_only=sources_only, stylesheet=stylesheet
		)
		entries.append((story, page.relative_to(site).as_posix()))

	web.write_catalog(site, entries)


def build_story(
	story_dir: Path,
	site: Path = Path(".dist"),
	*,
	sources_only: bool = False,
	stylesheet: Path | None = None,
) -> tuple[Story, Path]:
	"""Build one story’s editions and return its metadata and browser page path.

	With sources_only, keep an unpacked EPUB and Typst source for review.
	A distribution build writes a packaged EPUB and both PDF sizes.
	"""

	story = stories.load_story(story_dir)

	print(f"Loaded {story.title} by {story.author} ({story.published})")
	print(f"Language: {story.language}")
	print(f"Text length: {len(story.text)} characters")

	root = site / story_dir.parent.name / story_dir.name
	if stylesheet is None:
		stylesheet = web.write_stylesheet(site)
	stylesheet_href = stylesheet.relative_to(root / "web", walk_up=True).as_posix()

	if sources_only:
		with TemporaryDirectory() as tmp:
			epub.build_epub(story, story_dir, Path(tmp), unpack_root=site)
		pdf.write_print_source(story, root / "print")
	else:
		epub.build_epub(story, story_dir, site, unpack_root=None)
		pdf.write_pdfs(story, root / "print", story_dir.name, pdf.PAPER_SIZES)

	# Distribution pages link to sibling downloads. Preview pages link across to .dist/.
	download_root = Path("..")
	if sources_only:
		download_root = (
			Path("../../../../../.dist") / story_dir.parent.name / story_dir.name
		)

	page = web.write_story_page(
		story,
		story_dir,
		root / "web",
		download_root=download_root,
		stylesheet_href=stylesheet_href,
	)
	return story, page
