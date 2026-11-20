from datetime import UTC, datetime
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from ebooklib import epub

from miskatron.render import render_html, render_markdown
from miskatron.story import Story

# Modification date for the first eldritch.press EPUB edition.
EDITION_MODIFIED = datetime(2026, 11, 19, tzinfo=UTC)


def page(filename: str, title: str, body: str) -> epub.EpubHtml:
	document = epub.EpubHtml(file_name=filename, title=title)
	document.content = f"<html><body>{body}</body></html>"
	return document


def build_epub(
	story: Story,
	folder: Path,
	site: Path = Path(".dist"),
	*,
	unpack_root: Path | None = Path("stories/generated"),
) -> Path:
	key = Path(folder.parent.name) / folder.name
	book = epub.EpubBook()
	book.set_identifier(f"https://eldritch.press/{key.as_posix()}/")
	book.set_title(story.title)
	book.set_language(story.language)
	book.add_author(story.author)
	cover = folder / "cover.png"
	if cover.is_file():
		book.set_cover("cover.png", cover.read_bytes(), create_page=False)

	heading = f"<h1>{escape(story.title)}</h1>"
	title = page(
		"title.xhtml", "Title page", heading + f"<p>{escape(story.author)}</p>"
	)
	notes = (
		f"<h1>About this edition</h1><p>Originally published in {story.published}.</p>"
	)
	editorial = folder / "editorial.md"
	if editorial.is_file():
		notes += render_markdown(editorial.read_text(encoding="utf-8"))
	front = page("editorial.xhtml", "About this edition", notes)
	body = page("story.xhtml", story.title, heading + render_html(story))
	book.spine = [title, front, body]
	book.toc = book.spine
	book.guide = [{"type": "bodymatter", "item": body}]
	for item in [title, front, body, epub.EpubNav(), epub.EpubNcx()]:
		book.add_item(item)

	archive = site / key / "ebook" / f"{folder.name}.epub"
	archive.parent.mkdir(parents=True, exist_ok=True)
	with TemporaryDirectory() as work:
		staged = Path(work) / archive.name
		epub.write_epub(
			staged,
			book,
			{"mtime": EDITION_MODIFIED, "epub2_guide": False, "raise_exceptions": True},
		)
		if unpack_root is not None:
			output = unpack_root / key / "ebook"
			output.parent.mkdir(parents=True, exist_ok=True)
			tree = Path(work) / "contents"
			with ZipFile(staged) as package:
				package.extractall(tree)
			if output.exists():
				output.move(Path(work) / "previous")
			tree.move(output)
		staged.move(archive)
	return archive
