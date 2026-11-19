# eldritch.press

A little repo where I'm converting H.P. Lovecraft stories in the public domain to Markdown syntax.

Miskatron generates browser HTML, EPUBs, and printable A4 and A5 PDFs from those sources. Start with the [agent handoff](docs/handoff.md) for current
status and next steps, or the [publishing design](docs/specs/2026-11-18-epub-publishing-design.md)
for the agreed direction.

## Python development

Run `mise run bootstrap` to sync the uv environment and development dependencies.

- `mise run check` runs Ruff lint, formatting checks, ty type checking, and tests.
- `mise run test` runs the pytest suite.
- `mise run format` formats Python files using tabs and LF line endings.
- `mise run lint` runs Ruff lint and formatting checks only.
- `mise run typecheck` runs ty only.

Ruff uses its default lint rules plus import sorting. Tool versions are locked in
`uv.lock`.

## Building the website

`mise run build` runs `msk build ./stories/`. The directory is searched recursively for
`book.yaml` files. Pass a story or author directory to preview a smaller catalog. Each
site build replaces `build/` with the selected stories. Omitting the directory defaults to `./stories/`.

Each story has three directories under `<author>/<title>/`. In `build/`,
`web/` contains the browser page and assets, `ebook/` contains the unpacked EPUB,
and `print/` contains the print HTML, shared styles, and A4/A5 stylesheets.
For example, from a story's `build/.../print/` directory, run
`weasyprint --stylesheet a5.css index.html sample.pdf` to render the A5 edition.
In `dist/`, the web page links to the packaged EPUB in `ebook/` and PDFs in `print/`.

Run `mise run build` to preview the complete site at `build/index.html` and inspect the unpacked EPUBs.
Run `mise run dist` to assemble the distributable site and EPUB downloads in `dist/`. Open
`dist/index.html` to browse the catalog and download an EPUB from either the
catalog or its story page. GitHub Pages builds and deploys this directory on
pushes to `main`. Temporary files live in `build/`; distribution files are Git-ignored.

## Building an EPUB

From the repository root, run:

```sh
uv run msk build --format epub stories/lovecraft-h-p/the-tomb/
```

The book is written to `dist/lovecraft-h-p/the-tomb/ebook/the-tomb.epub`. Review its exact
unpacked contents under `build/lovecraft-h-p/the-tomb/ebook/`. Rebuilding
replaces that directory. Make corrections in the sources or generator.

The title page and publication note precede the story. Add an optional
`editorial.md` beside `book.yaml` to extend the note, and `cover.png` for a
library cover. The EPUB uses reader-default styling. Its identifier comes
from the author and story directory names. The initial edition uses a fixed
modification date in `src/miskatron/epub.py` for reproducible builds.

## Building PDFs

Install Pango before running the site build or tests (`brew install pango` on macOS).
On Ubuntu, install `libpango-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz-subset0`,
and `fonts-dejavu-core`. uv installs the WeasyPrint Python package.

The distribution includes A4 and A5 PDFs with download links in the catalog and
each story. WeasyPrint uses the story HTML and its stylesheet, with print rules
in `src/miskatron/styles/print.css` for pagination and margins. Pages are in
reading order. To generate only the A5 PDF under `dist/<author>/<title>/print/`, run:

```sh
uv run msk build --format pdf --paper A5 stories/lovecraft-h-p/the-tomb/
```

Omit `--paper` to generate both sizes.
