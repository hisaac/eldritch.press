"""Register the msk subcommands and report command failures to the terminal."""

import argparse
import subprocess

import yaml

from miskatron.commands import build, dist


def main() -> None:
	"""Parse the command line, call the selected handler, and report publishing errors with exit code 2."""

	parser = argparse.ArgumentParser(prog="msk")
	commands = parser.add_subparsers(dest="command", required=True)

	build.configure(
		commands.add_parser(
			"build", help="Build stories found recursively under a directory"
		)
	)
	dist.configure(
		commands.add_parser("dist", help="Build the complete distribution site")
	)

	args = parser.parse_args()

	# Each subparser attaches its own run function to the parsed arguments.
	try:
		args.run(args)
	except (
		OSError,
		ValueError,
		TypeError,
		subprocess.CalledProcessError,
		RuntimeError,
		yaml.YAMLError,
	) as error:
		parser.error(str(error))
