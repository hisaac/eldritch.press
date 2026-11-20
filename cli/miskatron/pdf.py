import json
import subprocess
from importlib.resources import as_file, files
from pathlib import Path
from tempfile import TemporaryDirectory

import pypandoc

from miskatron.render import render_html
from miskatron.story import Story

PAPER_SIZES = ("A4", "A5")


def pdf_name(slug: str, paper: str) -> str:
	return f"{slug}-{paper.lower()}.pdf"


def write_print_source(story: Story, output: Path) -> Path:
	output.mkdir(parents=True, exist_ok=True)
	source = output / "story.typ"
	with as_file(files("miskatron.templates").joinpath("story.typst")) as template:
		pypandoc.convert_text(
			render_html(story),
			format="html",
			to="typst",
			outputfile=source,
			extra_args=[
				"--wrap=none",
				f"--template={template}",
				f"--metadata=title:{story.title}",
				f"--variable=author-literal:{json.dumps(story.author, ensure_ascii=False)}",
				f"--variable=lang-literal:{json.dumps(story.language, ensure_ascii=False)}",
			],
		)
	return source


def write_pdfs(story: Story, output: Path, slug: str, sizes: tuple[str, ...]) -> None:
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
