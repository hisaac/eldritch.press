# eldritch.press

A little repo where I'm converting H.P. Lovecraft stories in the public domain to Markdown syntax.

Miskatron generates browser HTML, EPUBs, and printable A4 and A5 PDFs from those sources. Start with the [agent handoff](docs/handoff.md) for current
status and next steps, or the [publishing design](docs/specs/2026-11-18-epub-publishing-design.md)
for the agreed direction.

## Repository layout

- `stories/source/` holds the Markdown, metadata, and cover art for each story.
- `stories/generated/` holds the tracked catalog, browser pages, unpacked EPUBs, and print sources.
- `cli/` holds the Python project, including its conversion templates, styles, and tests.
- `docs/` holds project notes and publishing specs.
- `.dist/` holds the assembled site and downloads for GitHub Pages.

Run the commands below from the repository root.

## Python development

Run `mise install` to install Pandoc, Typst, and the project tools, then `mise deps install` to sync the Python environment.

- `mise run check` runs Ruff lint, formatting checks, ty type checking, and tests.
- `mise run test` runs the pytest suite.
- `mise run format` formats Python files using tabs and LF line endings.
- `mise run lint` runs Ruff lint and formatting checks only.
- `mise run typecheck` runs ty only.

Ruff uses its default lint rules plus import sorting. Tool versions are locked in
`cli/uv.lock`.

## Building the website

`mise run build` runs `msk build`. The directory is searched recursively for
`book.yaml` files. Pass a story or author directory to preview a smaller catalog. Each
site build replaces `stories/generated/` with the selected stories. Omitting the directory defaults to `./stories/source/`.

Each story has three directories under `<author>/<title>/`. In `stories/generated/`,
`web/` contains the browser page and assets, `ebook/` contains the unpacked EPUB,
and `print/story.typ` is the Typst source for both PDF sizes.
For example, from a story's `stories/generated/.../print/` directory, run
`typst compile --input paper=a5 story.typ sample.pdf` to render the A5 edition.
In `.dist/`, the web page links to the packaged EPUB in `ebook/` and PDFs in `print/`.

Run `mise run build` to preview the complete site at `stories/generated/index.html` and inspect the unpacked EPUBs.
Run `mise run dist` to assemble the distributable site and EPUB downloads in `.dist/`. Open
`.dist/index.html` to browse the catalog and download an EPUB from either the
catalog or its story page. GitHub Pages builds and deploys this directory on
pushes to `main`. Reviewable editions are tracked in Git. Python uses the system temporary directory for build work. Distribution files are Git-ignored.

## Building an EPUB

From the repository root, run:

```sh
mise exec -- msk build --format epub stories/source/lovecraft-h-p/the-tomb/
```

The book is written to `.dist/lovecraft-h-p/the-tomb/ebook/the-tomb.epub`. Review its exact
unpacked contents under `stories/generated/lovecraft-h-p/the-tomb/ebook/`. Rebuilding
replaces that directory. Make corrections in the sources or generator.

The title page and publication note precede the story. Add an optional
`editorial.md` beside `book.yaml` to extend the note, and `cover.png` for a
library cover. Pandoc packages the EPUB with a minimal `cli/styles/ebook.css` so readers control the typography. Its identifier comes
from the author and story directory names. The initial edition uses a fixed
modification date in `cli/miskatron/epub.py` for reproducible builds.

## Building PDFs

Pandoc reads the story Markdown and writes the browser HTML fragment. Miskatron
shares the typographically formatted fragment with the EPUB and Typst writers.
Jinja supplies the browser page and catalog layout. Browser printing uses
`cli/styles/story.css`; downloadable PDFs use `cli/templates/story.typst`,
with 17 mm margins and numbered pages in reading order.

To generate only the A5 PDF under `.dist/<author>/<title>/print/`, run:

```sh
mise exec -- msk build --format pdf --paper A5 stories/source/lovecraft-h-p/the-tomb/
```

Omit `--paper` to generate both sizes.
