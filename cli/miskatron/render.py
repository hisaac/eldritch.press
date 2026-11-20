"""Run Pandoc conversions for the HTML fragment, Typst source, and initial EPUB archive."""

import html
import json
from importlib import resources
from pathlib import Path

import pypandoc

from miskatron.story import Story


def generate_html(story: Story) -> str:
	"""Return the story body as an HTML fragment with Pandoc’s smart punctuation."""
	return _markdown_to_html(story.text)


def generate_typst_source(story: Story, source: Path) -> None:
	"""Write the Typst document that supplies the text and layout for both PDF sizes."""
	with resources.as_file(
		resources.files("miskatron.templates").joinpath("story.typst")
	) as template:
		pypandoc.convert_text(
			generate_html(story),
			format="html",
			to="typst",
			outputfile=source,
			extra_args=[
				"--wrap=none",
				f"--template={template}",
				f"--metadata=title:{story.title}",
				# The template inserts these values as quoted Typst strings.
				f"--variable=author-literal:{json.dumps(story.author, ensure_ascii=False)}",
				f"--variable=lang-literal:{json.dumps(story.language, ensure_ascii=False)}",
			],
		)


def generate_epub(
	story: Story, output: Path, *, source_dir: Path, identifier: str
) -> None:
	"""Write Pandoc’s EPUB with the edition notes, story body, and optional cover."""

	notes = f'<h1 id="editorial" epub:type="frontmatter">About this edition</h1><p>Originally published in {story.published}.</p>'
	editorial = source_dir / "editorial.md"
	if editorial.is_file():
		notes += _markdown_to_html(editorial.read_text(encoding="utf-8"))

	# EPUB navigation uses this heading ID to locate the start of the story.
	body = f'<h1 id="story">{html.escape(story.title)}</h1>\n{generate_html(story)}'

	cover = source_dir / "cover.png"
	with resources.as_file(
		resources.files("miskatron.styles").joinpath("ebook.css")
	) as stylesheet:
		pypandoc.convert_text(
			notes + "\n" + body,
			format="html",
			to="epub3",
			outputfile=output,
			extra_args=[
				"--wrap=none",
				f"--css={stylesheet}",
				f"--metadata=title:{story.title}",
				f"--metadata=author:{story.author}",
				f"--metadata=lang:{story.language}",
				f"--metadata=identifier:{identifier}",
				*([f"--epub-cover-image={cover}"] if cover.is_file() else []),
			],
		)


def _markdown_to_html(text: str) -> str:
	"""Convert story or editorial Markdown using the same block attributes and punctuation rules."""
	return pypandoc.convert_text(
		text,
		format="commonmark+attributes+smart",
		to="html5",
		extra_args=["--wrap=none"],
	)
