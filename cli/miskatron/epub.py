import re
from datetime import UTC, datetime
from html import escape
from importlib.resources import as_file, files
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.dom import minidom
from zipfile import ZipFile

import pypandoc

from miskatron.render import render_html, render_markdown
from miskatron.story import Story

EDITION_DATE = datetime(2026, 11, 19, tzinfo=UTC)


def add_story_landmark(nav: bytes) -> bytes:
	"""Link the EPUB landmarks menu to the same story opening as its TOC."""
	document = minidom.parseString(nav)
	links = document.getElementsByTagName("a")
	story_link = next(a for a in links if a.getAttribute("href").endswith("#story"))
	landmarks = next(
		n
		for n in document.getElementsByTagName("nav")
		if n.getAttribute("epub:type") == "landmarks"
	)
	item = document.createElement("li")
	link = document.createElement("a")
	link.setAttribute("href", story_link.getAttribute("href"))
	link.appendChild(document.createTextNode("Start of story"))
	link.setAttribute("epub:type", "bodymatter")
	item.appendChild(link)
	landmarks.getElementsByTagName("ol")[0].appendChild(item)
	return document.toxml(encoding="utf-8")


def build_epub(
	story: Story,
	folder: Path,
	site: Path = Path(".dist"),
	*,
	unpack_root: Path | None = Path("stories/generated"),
) -> Path:
	key = Path(folder.parent.name) / folder.name
	archive = site / key / "ebook" / f"{folder.name}.epub"
	archive.parent.mkdir(parents=True, exist_ok=True)
	notes = f'<h1 id="editorial" epub:type="frontmatter">About this edition</h1><p>Originally published in {story.published}.</p>'
	editorial = folder / "editorial.md"
	if editorial.is_file():
		notes += render_markdown(editorial.read_text(encoding="utf-8"))
	body = f'<h1 id="story">{escape(story.title)}</h1>\n{render_html(story)}'
	cover = folder / "cover.png"
	with (
		TemporaryDirectory(dir=archive.parent) as work,
		as_file(files("miskatron.styles").joinpath("ebook.css")) as stylesheet,
	):
		tmp = Path(work)
		raw = tmp / "pandoc.epub"
		pypandoc.convert_text(
			notes + "\n" + body,
			format="html",
			to="epub3",
			outputfile=raw,
			extra_args=[
				"--wrap=none",
				f"--css={stylesheet}",
				f"--metadata=title:{story.title}",
				f"--metadata=author:{story.author}",
				f"--metadata=lang:{story.language}",
				f"--metadata=identifier:https://eldritch.press/{key.as_posix()}/",
				*([f"--epub-cover-image={cover}"] if cover.is_file() else []),
			],
		)
		staged = tmp / "publication.epub"
		with ZipFile(raw) as source, ZipFile(staged, "w") as book:
			for entry in source.infolist():
				data = source.read(entry)
				if entry.filename == "EPUB/nav.xhtml":
					data = add_story_landmark(data)
				elif entry.filename == "EPUB/content.opf":
					# Pandoc supplies the build time for both edition dates.
					data, count = re.subn(
						rb'(<dc:date id="epub-date">|<meta property="dcterms:modified">)[^<]+',
						lambda match: (
							match[1]
							+ EDITION_DATE.strftime("%Y-%m-%dT%H:%M:%SZ").encode()
						),
						data,
					)
					if count != 2:
						raise ValueError(
							"Expected both Pandoc edition timestamps in the EPUB manifest"
						)
				entry.date_time = (
					EDITION_DATE.year,
					EDITION_DATE.month,
					EDITION_DATE.day,
					0,
					0,
					0,
				)
				book.writestr(entry, data)
		if unpack_root is not None:
			output = unpack_root / key / "ebook"
			output.parent.mkdir(parents=True, exist_ok=True)
			tree = tmp / "contents"
			with ZipFile(staged) as book:
				book.extractall(tree)
			previous = tmp / "previous"
			if output.exists():
				output.move(previous)
			try:
				tree.move(output)
			except OSError:
				if previous.exists():
					previous.move(output)
				raise
		staged.replace(archive)
	return archive
