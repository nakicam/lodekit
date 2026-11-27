# Documentation

The documentation site uses [MkDocs](https://www.mkdocs.org/) with
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/), and
[mkdocstrings](https://mkdocstrings.github.io/) for API reference. Its configuration is in
`mkdocs.yml`; the content lives in `docs/`.

```console
uv sync --group docs
uv run mkdocs serve          # live preview on http://127.0.0.1:8000
uv run mkdocs build --strict # what CI runs
```

- The build runs in `--strict` mode, so broken links and pages missing from `nav` fail CI.
- Link only to files inside `docs/` with relative links. Link to anything else in the repository
  with an absolute GitHub URL.
- API reference pages use mkdocstrings `::: lodekit.<package>.<module>` blocks. The handler resolves
  modules from `packages/*/src`, and docstrings follow the Google style enforced by ruff.
- Architecture decisions go into [`docs/decisions/`](../decisions/index.md) (MADR format).

!!! note "Material for MkDocs end of life"
    Material for MkDocs has announced its end of life for May 2027, and its successor is
    [Zensical](https://zensical.org/), which reads existing `mkdocs.yml` files. We stay on Material
    for now and will re-evaluate before that date.
