"""Handle msk dist, which builds the complete site for GitHub Pages."""

import argparse

from miskatron import publish


def configure(parser: argparse.ArgumentParser) -> None:
	"""Attach the distribution handler to the subparser."""
	parser.set_defaults(run=run)


def run(_args: argparse.Namespace) -> None:
	"""Build the site and downloads from the full story collection under stories/source/."""
	publish.build_distribution()
