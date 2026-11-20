"""Exercise the Markdown features that affect story text and typography across editions."""

from miskatron import render
from miskatron.story import Story


def test_smart_punctuation_in_prose_preserves_inline_code():
	"""Check smart punctuation in prose and literal punctuation inside inline code."""
	text = """"Don't wait..." she said---then typed `"wait..."`."""
	story = Story("Evening", "A. Writer", 1900, "en", text)

	assert render.generate_html(story) == (
		'<p>“Don’t wait…” she said—then typed <code>"wait..."</code>.</p>\n'
	)


def test_number_ranges_preserve_source_punctuation():
	"""Check single hyphens, literal en dashes, and Pandoc’s double-hyphen shorthand."""
	story = Story(
		"Evening", "A. Writer", 1900, "en", "[12-15](item-12-15), 3–2, and 4--6."
	)
	assert render.generate_html(story) == (
		'<p><a href="item-12-15">12-15</a>, 3–2, and 4–6.</p>\n'
	)


def test_poetry_class_applies_to_the_whole_quote():
	"""Keep verse lines and stanzas inside one marked quote, separate from its epigraph."""
	text = (
		"> Epigraph.\n\n{.poetry}\n> First line.\\\n> Second line.\n>\n> Next stanza."
	)
	story = Story("Evening", "A. Writer", 1900, "en", text)
	assert render.generate_html(story) == (
		"<blockquote>\n<p>Epigraph.</p>\n</blockquote>\n"
		'<blockquote class="poetry">\n<p>First line.<br />\nSecond line.</p>\n'
		"<p>Next stanza.</p>\n</blockquote>\n"
	)
