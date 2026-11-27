# Package layout

lodekit is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) with one
shared `uv.lock`. The root `pyproject.toml` is a *virtual* workspace root (`tool.uv.package = false`):
it holds shared tool configuration and dev dependencies and is never built or published.

Workspace members:

- `packages/*` - publishable distributions `lodekit-<name>`,
- `examples/*` - runnable examples (never published).

## Directory template

```text
packages/lodekit-<name>/
├── pyproject.toml
├── README.md
├── CHANGELOG.md            # maintained by release-please
├── LICENSE                 # copy of the root LICENSE
├── NOTICE                  # copy of the root NOTICE
├── src/
│   └── lodekit/            # NO __init__.py here (PEP 420 implicit namespace)
│       └── <name>/
│           ├── __init__.py
│           └── py.typed
└── tests/
    ├── unit/
    ├── contract/
    └── integration/
```

`lodekit/` must never contain an `__init__.py`, neither in a package nor in the future meta
package `lodekit`. Otherwise the namespace stops merging and other `lodekit-*` packages become
unimportable.

## `pyproject.toml` template

```toml
[project]
name = "lodekit-<name>"
version = "0.1.0"
description = "<one line>"
readme = "README.md"
requires-python = ">=3.11"
license = "Apache-2.0"
license-files = ["LICENSE", "NOTICE"]
authors = [{ name = "lodekit contributors" }]
classifiers = [
    "Development Status :: 2 - Pre-Alpha",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Typing :: Typed",
]
dependencies = [
    # other workspace packages: compatible range, resolved locally via [tool.uv.sources]
    "lodekit-common>=0.1,<0.2",
    # external packages: lower bound + upper bound at the next major (0.x: next minor)
    "pydantic>=2.7,<3",
]

[project.urls]
Homepage = "https://github.com/nakicam/lodekit"
Source = "https://github.com/nakicam/lodekit/tree/main/packages/lodekit-<name>"
Issues = "https://github.com/nakicam/lodekit/issues"

[build-system]
requires = ["uv_build>=0.12,<0.13"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "lodekit.<name>"

[tool.uv.sources]
lodekit-common = { workspace = true }
```

Rules:

- **Build backend:** `uv_build`, pinned with an upper bound as recommended by uv. Fall back to
  hatchling only if a build hook is needed (ADR-001).
- **Namespace:** `module-name = "lodekit.<name>"` makes `uv_build` package `src/lodekit/<name>`
  as part of the implicit namespace `lodekit`.
- **Inter-package dependencies** use compatible ranges (`>=0.1,<0.2` while in 0.x) in
  `[project.dependencies]` and are mapped to the local member with
  `[tool.uv.sources] <pkg> = { workspace = true }`. Published wheels therefore depend on released
  versions, while the workspace uses the local editable code.
- **Licence files:** `uv_build` only includes files inside the package directory, so `LICENSE` and
  `NOTICE` are copied into each package. CI checks that the copies match the root files.
- **No empty packages:** a package is only created when the current milestone needs it.

## Common commands

```bash
uv sync --all-packages                 # all members, editable, plus dev tools
uv run --package lodekit-<name> pytest # run inside one member
uv build --package lodekit-<name>      # build sdist + wheel into dist/
uv lock --check                        # verify uv.lock is up to date
```

The supported interpreter range is Python 3.11-3.14; `.python-version` pins 3.12 for local
development. Use `uv sync -p 3.11` (or any other supported version) to test another interpreter.

See also the [namespace packages spike](../spikes/0001-namespace-packages-mypy.md).
