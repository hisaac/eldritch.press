"""Finalize Pandoc’s EPUB with a story landmark and reproducible edition timestamps."""

import re
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from xml.dom import minidom
from zipfile import ZipFile

from miskatron import render
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
	"""Build the downloadable EPUB and return its path.

	When unpack_root is given, extract the finished archive there under
	<author>/<story>/ebook/ so its contents can be reviewed in Git.
	"""

	key = Path(folder.parent.name) / folder.name
	archive = site / key / "ebook" / f"{folder.name}.epub"
	archive.parent.mkdir(parents=True, exist_ok=True)

	with TemporaryDirectory(dir=archive.parent) as work:
		tmp = Path(work)
		raw = tmp / "pandoc.epub"
		render.generate_epub(
			story,
			raw,
			source_dir=folder,
			identifier=f"https://eldritch.press/{key.as_posix()}/",
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

				# ZIP entries also carry timestamps, independent of the book metadata.
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

			# Replacing the whole tree also removes obsolete files from older editions.
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
