from importlib.resources import as_file, files
from pathlib import Path
from tempfile import TemporaryDirectory

from weasyprint import CSS, HTML

from miskatron.render import render_web_page
from miskatron.story import Story

PAPER_SIZES = ("A4", "A5")


def pdf_name(slug: str, paper: str) -> str:
	return f"{slug}-{paper.lower()}.pdf"


def write_print_sources(
	story: Story, output: Path, sizes: tuple[str, ...], *, stylesheet_href: str
) -> Path:
	output.mkdir(parents=True, exist_ok=True)
	for paper in sizes:
		name = f"{paper.lower()}.css"
		style = files("miskatron.styles").joinpath(name)
		(output / name).write_bytes(style.read_bytes())
	page = output / "index.html"
	page.write_text(
		render_web_page(story, print_page=True, stylesheet_href=stylesheet_href),
		encoding="utf-8",
	)
	return page


def write_pdfs(story: Story, output: Path, slug: str, sizes: tuple[str, ...]) -> None:

	output.mkdir(parents=True, exist_ok=True)
	with (
		TemporaryDirectory() as tmp,
		as_file(files("miskatron.styles").joinpath("story.css")) as style,
	):
		page = write_print_sources(
			story, Path(tmp), sizes, stylesheet_href=style.resolve().as_uri()
		)
		document = HTML(filename=str(page))
		for paper in sizes:
			stylesheet = CSS(filename=str(page.with_name(f"{paper.lower()}.css")))
			document.write_pdf(output / pdf_name(slug, paper), stylesheets=[stylesheet])
