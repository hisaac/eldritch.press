# Miskatron Handoff

## Current publishing layout

Run `mise run build` to generate the tracked web, ebook, and print sources from `stories/source/` into `stories/generated/`. Run `mise run dist` to assemble the website and EPUB/PDF downloads in `.dist/`. GitHub Pages deploys that directory. Both commands stage work in Python’s default temporary directory. Git ignores `.dist/`. Pandoc converts the story Markdown to HTML and writes EPUB 3 and Typst. Typst compiles the tracked print source into A4 and A5 PDFs. The notes below describe the earlier HTML milestone.

## Working With the User

The user wants to learn Python by writing the implementation personally. Act as a guide: explain idioms, offer focused examples, inspect their work, and suggest the next small step. They have explicitly delegated tests, tooling, and documentation on occasion; that does not authorize taking over all implementation. Use long-form CLI flags when available. No automatic commits or pushes.

## Decisions to Preserve

- One story per publication; no collections.
- Shared Markdown text and sidecar `book.yaml` for HTML, EPUB, and eventual typeset zine PDFs. Language defaults to `en` only when absent.
- Fully generated outputs, with inspectable generated contents tracked for diffs. Never fix publications by hand-editing output.
- Standards-first EPUBs, minimal EPUB styling, editorial front matter before the story, and a standard `bodymatter` landmark. Reader-specific additions require a demonstrated need.
- Browser HTML is now the first milestone. It can have its own responsive styling. Print layout and booklet imposition remain undecided.
- Mise plus uv; Python selection in `.python-version`. Templates live inside the package. Documentation lives in `docs/`, specs in `docs/specs/`.

## What Exists

The current entry point is `msk = "miskatron.cli:main"`. From the repository root:

```sh
mise run sync
mise exec -- msk build stories/source/lovecraft-h-p/the-tomb/
mise run check
```

The build currently writes `index.html` and a copy of `story.css` under `generated/<author>/<story>/`, relative to the working directory. There is no EPUB or PDF generator yet. “The Tomb” and “The Quest of Iranon” are useful manual samples; “The Alchemist” is unfinished and contains legacy HTML and wrapped text.

`Story.from_files()` in `cli/miskatron/story.py` reads UTF-8 Markdown and YAML using PyYAML's `safe_load`, validates metadata, and returns a dataclass. A non-mapping YAML document raises `TypeError`; missing/invalid fields raise `ValueError`. The year must be exactly an integer, excluding booleans.

`render_html(story)` produces a fragment through markdown-it-py using CommonMark, raw HTML enabled, HTML output, and typography transformations disabled. `render_web_page(story)` wraps it with Jinja, then calls djLint's public `format_text` API using `load_config(".")`.

Jinja uses `PackageLoader`, autoescaping, `StrictUndefined`, and a trailing newline. `cli/templates/story.html` supplies document metadata and a `<main>` around the fragment; the fragment is marked `safe`. The template links to the packaged story stylesheet. The current raw-HTML-enabled parser differs from the earlier suggested disabled setting: do not silently change it, especially while unfinished sources contain HTML.

`cli/tests/test_story.py` contains nine parametrized test cases covering metadata, language defaults/overrides, missing title, invalid years, and source-text preservation. Fixtures are temporary fictional files: “The Sentient Teapot,” Professor Wobble, and Captain Noodle. They do not read or modify real stories.

## Next Useful Work

The most recent discussion was post-render HTML formatting. djLint is now installed and integrated by the user, but renderer/formatter tests have not been added. The next useful step is verifying that formatting preserves prose around inline elements, quotation marks and punctuation, explicit line breaks, Unicode, and any preformatted content. Also check metadata escaping, complete document structure, and repeatable output. Compare browser rendering as well as source diffs; source prettification must not change reading content.

After correctness checks, guide the user through a small browser stylesheet and inspect desktop/mobile readability. EPUB work resumes after the HTML page is useful. Do not introduce an abstract multi-format framework prematurely.

## Observed Follow-ups, Not Fixed During Handoff

- `cli.py` checks `story_file.is_file()` a second time where it intends to check `config_file.is_file()`. Missing configs are still caught when reading, but the dedicated check is wrong.
- Argument-parser `prog` still says `misk`, while the installed command is `msk`; build help says “Build a store EPUB” although it currently generates HTML.
- `render_html()` claims to render a complete page in its docstring, but returns a fragment.
- The template calls `content.rstrip('\\n')`: the doubled backslash means this deserves review against the intended newline trimming, particularly now that djLint formats the whole page.
- Output paths and djLint configuration discovery depend on the current working directory. Run from the repo root for now.

`mise run clean` removes generated output (including tracked output if present); `nuke` also runs `git clean -dX --force`, deleting ignored files such as `.env`. Neither is a verification step.

## Verification

During this documentation update, all nine loader tests passed, ty passed, and Ruff's formatting check passed. `mise run check` failed on Ruff I001 (import ordering) in `cli/miskatron/render.py`; implementation was left untouched. Remove the blank line between third-party imports and put a blank line before the local `miskatron.story` import, or apply Ruff's import fix when the user requests it.

These loader tests do not establish renderer correctness. No browser or EPUB validation was performed as part of this documentation update.
