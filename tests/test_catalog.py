from pathlib import Path

from miskatron.cli import build_all


def test_catalog_links_to_built_stories(tmp_path, monkeypatch):
	monkeypatch.chdir(tmp_path)
	for slug, title in [("first", "Zebra"), ("second", "Apple")]:
		folder = Path("stories/writer") / slug
		folder.mkdir(parents=True)
		(folder / "book.yaml").write_text(
			f"title: {title}\nauthor: Writer\npublished: 1900\n"
		)
		(folder / f"{slug}.md").write_text("Story text.")

	build_all()

	output = Path("generated")
	index = (output / "index.html").read_text()
	locations = []
	for slug, title in [("second", "Apple"), ("first", "Zebra")]:
		href = f"writer/{slug}/index.html"
		locations.append(index.index(f'<a href="{href}">{title}</a>'))
		assert f"<h1>{title}</h1>" in (output / href).read_text()
	assert locations == sorted(locations)
