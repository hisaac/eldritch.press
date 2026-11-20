"""Compile the shared Typst source into paper-sized PDF downloads."""

import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from miskatron import render
from miskatron.story import Story

PAPER_SIZES = ("A4", "A5")


def pdf_name(slug: str, paper: str) -> str:
	"""Return the download filename for a story slug and paper size."""
	return f"{slug}-{paper.lower()}.pdf"


def write_print_source(story: Story, output: Path) -> Path:
	"""Write story.typ in the output directory and return its path."""
	output.mkdir(parents=True, exist_ok=True)
	source = output / "story.typ"
	render.generate_typst_source(story, source)
	return source


def write_pdfs(story: Story, output: Path, slug: str, sizes: tuple[str, ...]) -> None:
	"""Compile all requested paper sizes before replacing any existing downloads."""
	output.mkdir(parents=True, exist_ok=True)
	with TemporaryDirectory(dir=output) as tmp:
		source = write_print_source(story, Path(tmp))
		for paper in sizes:
			name = pdf_name(slug, paper)
			subprocess.run(
				[
					"typst",
					"compile",
					"--input",
					f"paper={paper.lower()}",
					source,
					Path(tmp) / name,
				],
				check=True,
			)

		for paper in sizes:
			name = pdf_name(slug, paper)
			(Path(tmp) / name).replace(output / name)
