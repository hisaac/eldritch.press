"""Handle msk build for a selected story, author, or source directory."""

import argparse
from pathlib import Path

from miskatron import publish
from miskatron import story as stories
from miskatron.formats import epub, pdf


def configure(parser: argparse.ArgumentParser) -> None:
	"""Register the source directory, output format, and optional PDF paper size."""
	parser.add_argument(
		"directory", type=Path, nargs="?", default=Path("stories/source")
	)
	parser.add_argument("--format", choices=("html", "epub", "pdf"), default="html")

	parser.add_argument(
		"--paper",
		type=str.upper,
		choices=pdf.PAPER_SIZES,
		help="Paper size for --format pdf (default: both)",
	)
	parser.set_defaults(run=run)


def run(args: argparse.Namespace) -> None:
	"""Build a preview catalog or generate the requested downloads for each story found."""
	if args.paper and args.format != "pdf":
		raise ValueError("--paper requires --format pdf")

	folders = stories.discover_stories(args.directory)
	if args.format == "html":
		publish.build_site(folders, Path("stories/generated"), sources_only=True)
		return

	for folder in folders:
		story = stories.load_story(folder)
		if args.format == "epub":
			print(f"Wrote {epub.build_epub(story, folder)}")
		elif args.format == "pdf":
			pdf.write_pdfs(
				story,
				Path(".dist") / folder.parent.name / folder.name / "print",
				folder.name,
				(args.paper,) if args.paper else pdf.PAPER_SIZES,
			)
