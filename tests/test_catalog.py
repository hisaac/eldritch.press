from pathlib import Path

from miskatron.cli import build_all, build_story


def test_catalog_links_to_built_stories(tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)
	for author, slug, title in [
		("Writer", "first", "Zebra"),
		("Writer", "second", "Apple"),
		("Poet", "third", "Moon"),
	]:
		folder = Path("stories") / author.lower() / slug
		folder.mkdir(parents=True)
		(folder / "book.yaml").write_text(
			f"title: {title}\nauthor: {author}\npublished: 1900\n"
		)
		(folder / f"{slug}.md").write_text("Story text.")

	build_all()

	output = Path("generated")
	index = (output / "index.html").read_text()
	assert 'href="story.css"' in index
	assert (output / "story.css").is_file()
	assert index.count("<h2>Writer</h2>") == 1
	poet, writer = index.split("<h2>Writer</h2>")
	assert "<h2>Poet</h2>" in poet
	assert '<a href="poet/third/index.html">Moon</a>' in poet
	locations = []
	for slug, title in [("second", "Apple"), ("first", "Zebra")]:
		href = f"writer/{slug}/index.html"
		locations.append(writer.index(f'<a href="{href}">{title}</a>'))
		page = (output / href).read_text()
		assert page.index('href="../../index.html"') < page.index(f"<h1>{title}</h1>")
	assert locations == sorted(locations)


def test_story_cover_is_copied_and_removed_when_source_is_removed(
	tmp_path, monkeypatch
):
	monkeypatch.chdir(tmp_path)
	folder = Path("stories/writer/evening")
	folder.mkdir(parents=True)
	(folder / "book.yaml").write_text(
		"title: Evening\nauthor: A. Writer\npublished: 1900\n"
	)
	(folder / "evening.md").write_text("Story text.")
	cover = folder / "cover.png"
	cover.write_bytes(b"fictional cover image")

	_, page = build_story(folder)
	html = page.read_text()
	assert 'src="cover.png"' in html
	assert 'alt="Cover of Evening"' in html
	assert html.index('src="cover.png"') < html.index("Story text.")
	assert (page.parent / "cover.png").read_bytes() == cover.read_bytes()

	cover.unlink()
	build_story(folder)
	assert 'src="cover.png"' not in page.read_text()
	assert not (page.parent / "cover.png").exists()
