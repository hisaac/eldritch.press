from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory

from weasyprint import CSS, HTML

from miskatron.render import render_web_page
from miskatron.story import Story

PAPER_SIZES = ("A4", "A5")


def pdf_name(slug: str, paper: str) -> str:
	return f"{slug}-{paper.lower()}.pdf"


def write_print_sources(story: Story, output: Path, sizes: tuple[str, ...]) -> Path:
	output.mkdir(parents=True, exist_ok=True)
	for name in (
		"story.css",
		"print.css",
		*(f"{paper.lower()}.css" for paper in sizes),
	):
		style = files("miskatron").joinpath("styles", name)
		(output / name).write_bytes(style.read_bytes())
	page = output / "index.html"
	page.write_text(render_web_page(story, print_page=True), encoding="utf-8")
	return page


def write_pdfs(story: Story, output: Path, slug: str, sizes: tuple[str, ...]) -> None:

	output.mkdir(parents=True, exist_ok=True)
	with TemporaryDirectory() as tmp:
		page = write_print_sources(story, Path(tmp), sizes)
		document = HTML(filename=str(page))
		for paper in sizes:
			stylesheet = CSS(filename=str(page.with_name(f"{paper.lower()}.css")))
			document.write_pdf(output / pdf_name(slug, paper), stylesheets=[stylesheet])
