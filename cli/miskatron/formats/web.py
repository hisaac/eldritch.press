"""Build the browser catalog and story pages with links to their downloadable editions."""

import shutil
import subprocess
from importlib import resources
from pathlib import Path

import jinja2

from miskatron import render
from miskatron.formats import pdf
from miskatron.story import Story

environment = jinja2.Environment(
	loader=jinja2.PackageLoader("miskatron.templates", "."),
	autoescape=jinja2.select_autoescape(("html", "xml", "xhtml")),
	undefined=jinja2.StrictUndefined,
	keep_trailing_newline=True,
)


def render_web_page(
	story: Story,
	*,
	stylesheet_href: str = "story.css",
	epub_href: str = "",
	pdf_links: list[tuple[str, str]] | None = None,
	has_cover: bool = False,
) -> str:
	"""Place the story fragment, metadata, and download links into a complete HTML document."""
	template = environment.get_template("story.html")
	html = template.render(
		story=story,
		stylesheet_href=stylesheet_href,
		has_cover=has_cover,
		epub_href=epub_href,
		pdf_links=pdf_links or [],
		content=render.generate_html(story),
	)

	return format_publication_file(html, "index.html")


def format_publication_file(content: str, filename: str) -> str:
	"""Format generated HTML or CSS using the packaged Prettier settings for the given filename."""
	result = subprocess.run(
		[
			"prettier",
			"--stdin-filepath",
			filename,
			"--config",
			Path(__file__).with_name(".prettierrc.yaml"),
			"--no-editorconfig",
		],
		input=content,
		encoding="utf-8",
		stdout=subprocess.PIPE,
		check=True,
	)
	return result.stdout


def write_catalog(site: Path, entries: list[tuple[Story, str]]) -> None:
	"""Group the supplied story links by author in the catalog, with titles sorted within each group."""
	entries.sort(key=lambda entry: entry[0].title.casefold())
	template = environment.get_template("index.html")
	html = format_publication_file(template.render(entries=entries), "index.html")
	index = site / "index.html"
	index.parent.mkdir(exist_ok=True)
	index.write_text(html, encoding="utf-8")


def write_story_page(
	story: Story,
	story_dir: Path,
	output_dir: Path,
	*,
	download_root: Path,
	stylesheet_href: str,
) -> Path:
	"""Write the browser page and sync its optional cover, returning the path to index.html."""
	cover = story_dir / "cover.png"
	html = render_web_page(
		story,
		has_cover=cover.is_file(),
		stylesheet_href=stylesheet_href,
		epub_href=(download_root / "ebook" / f"{story_dir.name}.epub").as_posix(),
		pdf_links=[
			(
				paper,
				(
					download_root / "print" / pdf.pdf_name(story_dir.name, paper)
				).as_posix(),
			)
			for paper in pdf.PAPER_SIZES
		],
	)
	output_dir.mkdir(parents=True, exist_ok=True)

	if cover.is_file():
		shutil.copyfile(cover, output_dir / "cover.png")
	else:
		(output_dir / "cover.png").unlink(missing_ok=True)

	output_file = output_dir / "index.html"
	output_file.write_text(html, encoding="utf-8")

	return output_file


def write_stylesheet(output_dir: Path) -> Path:
	"""Write the shared story.css to the site directory and return its path."""
	stylesheet = resources.files("miskatron.styles").joinpath("story.css")
	css = format_publication_file(stylesheet.read_text(encoding="utf-8"), "story.css")
	output_dir.mkdir(parents=True, exist_ok=True)
	path = output_dir / "story.css"
	path.write_text(css, encoding="utf-8")
	return path
