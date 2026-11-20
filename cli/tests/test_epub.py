"""Check EPUB packaging, navigation, and reading order using a fictional story."""

from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from miskatron import cli


def test_epub_build(tmp_path, monkeypatch):
	"""Compare the unpacked tree with the archive and inspect the rebuilt book’s text and navigation."""

	monkeypatch.chdir(tmp_path)
	folder = Path("stories/source/writer/evening")
	folder.mkdir(parents=True)
	(folder / "book.yaml").write_text(
		"title: Night & Day\nauthor: A. Writer\npublished: 1900\nlanguage: fr\n"
	)
	(folder / "evening.md").write_text("> Voilà!\\\n> Après.\n\nBefore *dawn*, again.")
	(folder / "editorial.md").write_text("An *edition* note.")
	monkeypatch.setattr("sys.argv", ["msk", "build", "--format", "epub", str(folder)])
	cli.main()

	root = Path("stories/generated/writer/evening/ebook")
	archive = Path(".dist/writer/evening/ebook/evening.epub")
	with ZipFile(archive) as package:
		expected = {name: package.read(name) for name in package.namelist()}

	def contents():
		"""Map each unpacked file’s archive-relative name to its exact bytes."""
		return {
			p.relative_to(root).as_posix(): p.read_bytes()
			for p in root.rglob("*")
			if p.is_file()
		}

	assert contents() == expected
	(root / "obsolete.xhtml").touch()
	cli.main()
	assert contents() == expected

	ns = {"h": "http://www.w3.org/1999/xhtml", "e": "http://www.idpf.org/2007/ops"}
	body = ET.parse(root / "EPUB/text/ch002.xhtml")
	assert body.getroot().get("lang") == "fr"
	assert [el.text for el in body.findall(".//h:h1", ns)] == ["Night & Day"]
	line = body.find(".//h:blockquote/h:p", ns)
	assert line is not None and line.text == "Voilà!"
	assert line[0].tag.endswith("}br") and line[0].tail == "\nAprès."
	assert "Before dawn, again." in "".join(body.getroot().itertext())

	front = ET.parse(root / "EPUB/text/ch001.xhtml")
	assert front.findtext(".//h:em", namespaces=ns) == "edition"
	nav = ET.parse(root / "EPUB/nav.xhtml")
	target = nav.find(".//h:a[@e:type='bodymatter']", ns)
	assert target is not None and target.get("href") == "text/ch002.xhtml#story"

	# The manifest maps IDs to files. The spine lists those IDs in reading order.
	opf = ET.parse(root / "EPUB/content.opf")
	items = {
		item.get("id"): item.get("href")
		for item in opf.findall(".//{*}manifest/{*}item")
	}
	assert [
		items[ref.get("idref")] for ref in opf.findall(".//{*}spine/{*}itemref")
	] == ["text/title_page.xhtml", "text/ch001.xhtml", "text/ch002.xhtml"]
