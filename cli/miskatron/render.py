import subprocess
from pathlib import Path

import regex
import smartypants
from jinja2 import Environment, PackageLoader, StrictUndefined, select_autoescape
from markdown_it.main import MarkdownIt
from mdit_py_plugins.attrs import attrs_block_plugin

from miskatron.story import Story

environment = Environment(
	loader=PackageLoader("miskatron.templates", "."),
	autoescape=select_autoescape(("html", "xml", "xhtml")),
	undefined=StrictUndefined,
	keep_trailing_newline=True,
)


def render_web_page(
	story: Story,
	*,
	stylesheet_href: str = "story.css",
	epub_href: str = "",
	pdf_links: list[tuple[str, str]] | None = None,
	print_page: bool = False,
	has_cover: bool = False,
) -> str:
	template = environment.get_template("story.html")
	html = template.render(
		story=story,
		stylesheet_href=stylesheet_href,
		has_cover=has_cover,
		epub_href=epub_href,
		pdf_links=pdf_links or [],
		print_page=print_page,
		content=render_html(story),
	)

	return format_publication_file(html, "index.html")


def format_publication_file(content: str, filename: str) -> str:
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


def render_html(story: Story) -> str:
	"""Render the story body with typographic punctuation."""
	return render_markdown(story.text)


def render_markdown(text: str) -> str:
	parser = MarkdownIt(
		"commonmark",
		{
			"html": True,
			"xhtmlOut": False,
			"typographer": False,
		},
	)
	parser.use(attrs_block_plugin, allowed=["class"])
	fragment = parser.render(text)
	fragment = format_em_dashes(fragment)
	fragment = format_ellipses(fragment)
	fragment = format_quotes(fragment)
	fragment = format_number_ranges(fragment)
	fragment = add_en_dash_word_joiners(fragment)
	return fragment


def format_em_dashes(fragment: str) -> str:
	return smartypants.smartypants(fragment, smartypants.Attr.d)


def format_ellipses(fragment: str) -> str:
	return smartypants.smartypants(fragment, smartypants.Attr.e)


def format_quotes(fragment: str) -> str:
	# Decode Markdown's &quot; and emit Unicode for all three Smartypants passes.
	flags = smartypants.Attr
	return smartypants.smartypants(fragment, flags.q | flags.b | flags.w | flags.u)


def format_number_ranges(fragment: str) -> str:
	# Skip numeric identifiers and URLs inside markup.
	return regex.sub(r"(?<!<[^>]*)([0-9]+)-([0-9]+)", r"\1–\2", fragment)


def add_en_dash_word_joiners(fragment: str) -> str:
	word_joiner = "\u2060"
	return regex.sub(
		f"{word_joiner}?–{word_joiner}?", f"{word_joiner}–{word_joiner}", fragment
	)
