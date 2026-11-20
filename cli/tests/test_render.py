from miskatron.render import render_html, render_markdown
from miskatron.story import Story


def test_smart_punctuation_in_prose_preserves_inline_code():
	text = """"Don't wait..." she said--then typed `"wait..."`."""
	story = Story("Evening", "A. Writer", 1900, "en", text)

	assert render_html(story) == (
		'<p>“Don’t wait…” she said—then typed <code>"wait..."</code>.</p>\n'
	)


def test_number_ranges_follow_standard_ebooks_rules():
	text = "[12-15](item-12-15) and a 3-2 score. Already 4\u2060–\u20606."
	story = Story("Evening", "A. Writer", 1900, "en", text)

	assert render_html(story) == (
		'<p><a href="item-12-15">12\u2060–\u206015</a> and a 3\u2060–\u20602 score. '
		"Already 4\u2060–\u20606.</p>\n"
	)


def test_poetry_class_applies_to_the_whole_quote():
	text = (
		"> Epigraph.\n\n{.poetry}\n> First line.\\\n> Second line.\n>\n> Next stanza."
	)
	assert render_markdown(text) == (
		"<blockquote>\n<p>Epigraph.</p>\n</blockquote>\n"
		'<blockquote class="poetry">\n<p>First line.<br />\nSecond line.</p>\n'
		"<p>Next stanza.</p>\n</blockquote>\n"
	)
