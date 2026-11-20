# Repository Guidelines

## Collaboration Style

The user is learning Python and wants to write implementation code personally. Default to explanations, small examples, reviews, and suggested next steps. Edit implementation only when explicitly asked; requests for tests, tooling, or documentation authorize those changes. Explain Python idioms plainly. Prefer long-form command flags where available.

Read [the handoff](docs/handoff.md) for current status and [the publishing design](docs/specs/2026-11-18-epub-publishing-design.md) for decisions. Keep specs in `docs/specs/`.

## Project Structure

Miskatron publishes individual public-domain stories. Pandoc produces HTML, EPUB, and Typst source. Typst compiles A4 and A5 PDFs. Collections are out of scope.

- `stories/source/<author>/<story>/<story>.md`: authoritative story text.
- `book.yaml` beside each story: title, author, integer publication year, and optional language (defaults to `en`).
- `cli/miskatron/`: Python package; `cli.py` handles arguments and output, `story.py` loads metadata/text, and `render.py` renders HTML using `cli/templates/story.html`.
- `cli/tests/`: pytest tests using fictional data and temporary files.
- `stories/generated/`: tracked web, unpacked EPUB, and print sources for review.
- `.dist/`: assembled website and downloadable EPUBs, deployed by GitHub Pages.
- `reference/`: archived sources; preserve unless explicitly working on them.

## Development Commands

Mise reads Python from `.python-version`; uv manages dependencies, `.venv`, and `cli/uv.lock`. The installed command is **`msk`**, despite older references to `misk`.

- `mise install` and `mise deps install`: install project tools and Python dependencies.
- `mise run check`: lint, formatting, type checks, and tests.
- `mise run test`: pytest.
- `mise run format`: format Mise configuration and Python.
- `mise run typecheck`: ty.
- `mise exec -- msk build stories/source/lovecraft-h-p/the-tomb/`: generate HTML; run from the repository root.

`clean` deletes generated/build output. `nuke` also deletes Git-ignored files, including `.venv` and `.env`; do not run either as routine verification.

## Style and Verification

Follow `.editorconfig`: UTF-8, LF, tabs, final newline, no trailing whitespace. Ruff handles Python formatting and linting, including import sorting. Use lowercase hyphenated story paths. Preserve wording, punctuation, and semantic Markdown structure.

Keep story loading independent of output formats. Generated publications must be reproducible from sources; fix generators rather than hand-editing output. Test meaningful behavior with fake data, including text and inline-whitespace preservation. Run relevant checks before claiming completion.

## Commits and Reviews

Use short, descriptive commit subjects matching history. Keep changes focused. Describe behavior, verification, and any regenerated output changes. Do not commit or push unless requested.
