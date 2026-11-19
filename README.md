# eldritch.press

A little repo where I'm converting H.P. Lovecraft stories in the public domain to Markdown syntax.

Miskatron currently generates browser HTML from those sources; EPUB and printable
zine PDFs are planned. Start with the [agent handoff](docs/handoff.md) for current
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
