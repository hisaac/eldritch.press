# Individual-Story Publishing: EPUB, Print, and HTML

Status: Approved. This documents the agreed direction and first milestone; it is not an implementation plan. Library and tooling details identified below remain for implementation planning.

## Current Milestone Update

The user subsequently chose browser HTML as the first milestone because it is easier to inspect and verify. Source loading, Markdown conversion, Jinja page rendering, and djLint post-render formatting are implemented. See [the handoff](../handoff.md) for current code behavior and follow-up work. The EPUB acceptance criteria below remain the later EPUB milestone, not the current implementation status.

The installed CLI command is now `msk` (package: `miskatron`).

## Intent and Agreed Decisions

Build Miskatron, a Python publishing tool for individual short stories. Use `miskatron` as the Python package name and `msk` as the CLI command. Developing and learning from the tool is part of the project's purpose. Each story produces its own ebook; collections are outside the intended scope.

Also support typeset PDF editions of individual stories for printing as zines and styled HTML editions for reading in a browser. These are agreed future requirements; the first implementation milestone is now browser HTML, followed by EPUB.

Markdown remains the authoritative story text. EPUB contents must be fully generated, with no manual edits required. Editorial information precedes the story in reading order, while a standard EPUB `bodymatter` landmark identifies the story's beginning as the preferred initial reading location. Reading systems ultimately control initial opening behavior.

Prefer standards over reader-specific extensions. Start without Apple's proprietary start-page marker. Add compatibility measures only in response to demonstrated problems and an explicit decision.

For EPUB, use minimal styling that respects reader preferences. Preserve meaningful structure, including emphasis, quotations, scene breaks, and explicit line breaks. Avoid embedded body fonts, forced colors, and unnecessary overrides of reader settings. Do not silently rewrite spelling or punctuation. Print editions will need deliberate typography and page layout, separate from the EPUB styling policy.

Use Mise for tool management, continuing the existing `mise.toml` convention, and uv for Python project environments, dependency management, locking, and command execution. Track generated EPUB contents in Git so changes to the publishing tools can be reviewed alongside changes to their output.

## Approaches Considered

- **Standard Ebooks:** established production tooling, but requires a Markdown-to-project bridge and brings conventions this project wants freedom to explore independently.
- **Python with Pandoc:** a direct conversion route, but offers less opportunity to build and understand the publication machinery.
- **Python with an EPUB library — selected:** control over generation and a useful learning project, with responsibility for metadata, navigation, and reader compatibility. EbookLib is the initial candidate, not a confirmed dependency.

## Proposed Repository Layout

This section records the original proposal. See the [README](../../README.md) for the current repository layout and commands.

Story sources have moved to `src/stories/`. The following layout describes the intended publishing structure; `build.py`, editorial files, and EPUB packaging are not implemented yet:

```text
src/stories/lovecraft-h-p/the-tomb/
  the-tomb.md
  editorial.md
  book.yaml                  # shared story metadata and edition configuration
src/miskatron/             # Python CLI and publishing code
  __init__.py
  cli.py                    # arguments, commands, user-facing errors
  build.py                  # publication generation
  templates/
  styles/
tests/
generated/lovecraft-h-p/the-tomb/  # tracked, unpacked EPUB contents
dist/                       # ignored, packaged .epub files
reference/                  # existing archived sources
docs/specs/
mise.toml
pyproject.toml               # project metadata, dependencies, msk entry point
uv.lock                     # tracked dependency lockfile
```

`src/stories/` describes the source's purpose and accommodates editorial text or future cover assets. `generated/` makes the generated status explicit. Keep archived sources in `reference/`; do not reorganize them as part of the first milestone.

The agreed source format uses a sidecar `book.yaml` for story title, author, original publication year, and language (defaulting to `en`). Markdown contains the story text without duplicated YAML front matter. EPUB, PDF, and HTML generation should consume this same source and metadata. `editorial.md` supplies human-authored source and edition notes. Its exact contents remain to be written. Distinguish original publication information from edition metadata.

## Browser HTML Output (Current Milestone)

Generate complete HTML documents with appropriate browser styling so individual stories can be read on desktop and mobile screens. Keep these editions fully generated from the shared Markdown and metadata, with no separate transcription or manual output edits.

Use semantic HTML and responsive, accessible reading layouts. Browser templates and CSS may provide typography and layout distinct from the minimal EPUB styles and fixed print pages. Reuse Markdown conversion where practical, while keeping browser documents independent of EPUB packaging and navigation conventions.

Keep the `Story` model free of browser layout concerns. The HTML renderer is implemented; no website framework or deployment infrastructure is required. Browser styling, asset packaging, and final output layout remain to be decided. Publishing a hosted website is a separate decision.

## Future PDF and Zine Output

Generate typeset PDFs suitable for printing individual stories as zines, without maintaining a separate transcription or hand-editing generated output.

Keep the `Story` model and source loading independent of EPUB libraries, XHTML packaging, and print layout. Output-specific rendering should consume the loaded story and shared metadata. Preserve semantic Markdown structure so each output can present it appropriately. Do not add renderer frameworks or PDF dependencies before they are needed.

Before implementing print output, choose a typesetting engine and decide page size, fonts, margins, front matter, and pagination. Clarify whether to produce PDFs in reading order, imposed booklet sheets (pages rearranged for printing and folding), or both; also settle duplex printing and binding expectations. These are open design choices, not current implementation requirements.

Plan to review rendered pages and a physical folded print sample. Decide which inspectable PDF-generation intermediates to track for output diffs; the existing commitment to track unpacked EPUB contents does not automatically require checking in binary PDFs.

## Planned EPUB Generation and Reviewable Output

The current build command generates HTML. EPUB command selection is still to be designed; the existing invocation through the Mise-managed environment is:

```sh
mise exec -- uv run msk build src/stories/lovecraft-h-p/the-tomb/
```

The planned EPUB build will read the source, validate required metadata, render XHTML and navigation, and write the complete unpacked EPUB tree plus its packaged `.epub`. Publication order is title page, editorial information, then story. Navigation exposes the front matter and story; the `bodymatter` landmark targets the story title and opening text.

**Proposal: track the entire unpacked EPUB tree**, including packaging metadata, XHTML, CSS, and any included images. Ignore the ZIP-based `.epub` artifacts in `dist/`; they can be rebuilt and do not provide useful textual diffs. This satisfies the requested output-review workflow without tracking two copies of the same publication.

The tracked tree must represent the actual packaged contents, not an approximate preview. Regeneration must remove stale generated files within the selected book's output directory, without touching other books or source files. Mark generated files as non-editable in contributor documentation rather than inserting comments that alter publication content.

Use stable identifiers, deterministic ordering, and consistent serialization. Do not inject current timestamps, random identifiers, or machine-specific paths on every build. Choose an explicit, stable source for required EPUB modification metadata. Byte-identical ZIP archives are not a first-milestone requirement; identical inputs must produce identical unpacked output.

Tool changes should include regenerated output in the same review. A later automated check can rebuild tracked publications and fail on unexpected differences.

## Later EPUB Milestone and Acceptance

Publish “The Tomb” end to end. Confirm the EPUB library can support standards-based landmarks and a faithful unpacked output tree before building abstractions around it. If it cannot, revisit the library choice.

The milestone is complete when:

- One command produces an inspectable publication tree and EPUB without manual repairs.
- The text, epigraph, explicit line break, and metadata survive conversion correctly, without a duplicated story heading.
- Front matter precedes the story and navigation identifies the story's start.
- EPUBCheck reports no errors; warnings are reviewed.
- Repeated builds leave tracked output unchanged when inputs are unchanged.
- Automated checks cover content preservation, navigation targets, and deterministic output.
- Manual checks in Apple Books, Thorium, and the user's Kobo assess navigation, initial opening, font resizing, themes, and paragraph rendering. Record device results rather than assuming desktop behavior proves compatibility.

## Tooling and Remaining Decisions

Mise reads Python from `.python-version` (currently `3.15`) and manages uv and additional tools. uv manages the project environment and locked dependencies. `pyproject.toml` declares the `msk` entry point. Runtime dependencies currently include PyYAML, markdown-it-py, Jinja2, and djLint; development dependencies include pytest, Ruff, and ty. Standard Ebooks is not a build dependency.

Markdown parsing and sidecar metadata are implemented. Remaining EPUB decisions include stable publication identifiers, modification dates, packaging, and library selection. The directory migration is complete. Avoid adding collections, cover-generation systems, watch mode, plugin frameworks, or general-purpose styling configuration without a concrete need.

## References

- [EPUB 3.3 landmarks](https://www.w3.org/TR/epub-33/#sec-nav-landmarks)
- [EbookLib tutorial](https://docs.sourcefabric.org/projects/ebooklib/en/latest/tutorial.html)
- [EPUBCheck](https://www.w3.org/publishing/epubcheck/docs/getting-started/)
