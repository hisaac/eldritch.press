from pathlib import Path

from miskatron.cli import build_all, build_story, main


def test_catalog_links_to_built_stories(tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)
	for author, slug, title in [
		("Writer", "first", "Zebra"),
		("Writer", "second", "Apple"),
		("Poet", "third", "Moon"),
	]:
		folder = Path("stories/source") / author.lower() / slug
		folder.mkdir(parents=True)
		(folder / "book.yaml").write_text(
			f"title: {title}\nauthor: {author}\npublished: 1900\n"
		)
		(folder / f"{slug}.md").write_text("Story text.")

	build_all()
	assert not Path(".dist").exists()
	assert Path("stories/generated/writer/first/ebook/EPUB/story.xhtml").is_file()
	assert Path("stories/generated/writer/first/print/index.html").is_file()
	assert Path("stories/generated/writer/first/print/a5.css").is_file()
	assert not list(Path("stories/generated").rglob("*.epub"))
	assert not list(Path("stories/generated").rglob("*.pdf"))
	build_all(Path(".dist"))
	assert not Path(".build").exists()
	preview_index = Path("stories/generated/index.html").read_text()

	output = Path(".dist")
	index = (output / "index.html").read_text()
	for catalog in (preview_index, index):
		assert '.epub"' not in catalog
		assert '.pdf"' not in catalog
	assert 'href="story.css"' in index
	for root in (Path("stories/generated"), output):
		assert list(root.rglob("story.css")) == [root / "story.css"]
		for page in root.glob("*/*/*/index.html"):
			assert 'href="../../../story.css"' in page.read_text()
			assert (page.parent / "../../../story.css").samefile(root / "story.css")
	assert index.count("<h2>Writer</h2>") == 1
	poet, writer = index.split("<h2>Writer</h2>")
	assert "<h2>Poet</h2>" in poet
	assert '<a href="poet/third/web/index.html">Moon</a>' in poet
	for section, count in [(poet, 1), (writer, 2)]:
		assert section.count("<ul>") == 1
		assert section.count("<li>") == count
	locations = []
	for slug, title in [("second", "Apple"), ("first", "Zebra")]:
		href = f"writer/{slug}/web/index.html"
		locations.append(writer.index(f'<a href="{href}">{title}</a>'))
		page = (output / href).read_text()
		preview = (Path("stories/generated") / href).read_text()
		for asset in (
			f"ebook/{slug}.epub",
			f"print/{slug}-a4.pdf",
			f"print/{slug}-a5.pdf",
		):
			assert f'href="../../../../../.dist/writer/{slug}/{asset}"' in preview
		assert page.index('href="../../../index.html"') < page.index(
			f"<h1>{title}</h1>"
		)
		assert f'href="../ebook/{slug}.epub"' in page
		assert (output / "writer" / slug / "ebook" / f"{slug}.epub").is_file()
		for size in ["a4", "a5"]:
			name = f"{slug}-{size}.pdf"
			assert f'href="../print/{name}"' in page
			assert (
				(output / "writer" / slug / "print" / name)
				.read_bytes()
				.startswith(b"%PDF-")
			)
	assert not list(output.rglob("*.xhtml"))
	assert locations == sorted(locations)


def test_story_cover_is_copied_and_removed_when_source_is_removed(
	tmp_path, monkeypatch
):
	monkeypatch.chdir(tmp_path)
	folder = Path("stories/source/writer/evening")
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


def test_build_directory_recursively(tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)
	for slug in ("first", "second"):
		folder = Path("library/group/writer") / slug
		folder.mkdir(parents=True)
		(folder / "book.yaml").write_text(
			f"title: {slug}\nauthor: Writer\npublished: 1900\n"
		)
		(folder / f"{slug}.md").write_text("Story.")
	for source, titles in [
		("library", ["first", "second"]),
		("library/group/writer/second", ["second"]),
	]:
		monkeypatch.setattr("sys.argv", ["msk", "build", source])
		main()
		assert (
			sorted(
				p.parent.parent.name
				for p in Path("stories/generated").rglob("ebook/mimetype")
			)
			== titles
		)
		assert not Path(".dist").exists()
