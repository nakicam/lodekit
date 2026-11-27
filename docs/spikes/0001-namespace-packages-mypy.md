# Spike 0001: PEP 420 namespace packages with uv_build and mypy --strict

- Date: 2026-11-27
- Issue: #2 (M0-2), risk 1 of ADR-001
- Tools: uv 0.12.3, uv_build `>=0.12,<0.13`, mypy 2.4.1, Windows 11, CPython 3.11 / 3.12 / 3.13 / 3.14

## Question

Do two workspace members sharing the implicit namespace `lodekit` (no `lodekit/__init__.py`)
build, install editable, import together and pass `mypy --strict`?

## Setup

A throwaway uv workspace with two members built by `uv_build`:

- `lodekit-alpha` with `module-name = "lodekit.alpha"`, `src/lodekit/alpha/{__init__.py,py.typed}`,
- `lodekit-beta` with `module-name = "lodekit.beta"`, depends on `lodekit-alpha>=0.1,<1` with
  `[tool.uv.sources] lodekit-alpha = { workspace = true }`, and calls `lodekit.alpha.a()`.

Root: `tool.uv.package = false`, `members = ["packages/*"]`, `[tool.mypy] strict = true`.

## Results

| Check | Result |
|---|---|
| `uv sync --all-packages` on 3.11, 3.12, 3.13, 3.14 | pass |
| Editable imports `lodekit.alpha` + `lodekit.beta` together; `lodekit.__path__` lists both `src/lodekit` dirs | pass |
| `uv build --package lodekit-beta`: wheel contains `lodekit/beta/...` and **no** `lodekit/__init__.py` | pass |
| `mypy --strict -p lodekit.alpha -p lodekit.beta` (installed editable packages) | pass, all versions |
| `mypy --strict packages/lodekit-beta/src` (single package path) | pass |
| `mypy --strict packages/lodekit-alpha/src packages/lodekit-beta/src` (several src paths, no `mypy_path`) | **fail**: "Source file found twice under different module names: `alpha` and `lodekit.alpha`" |
| Same with `explicit_package_bases = true` and `mypy_path` listing every `packages/*/src` | pass |

## Consequences

- `uv_build` with a dotted `module-name` is suitable for all lodekit packages; no hatchling needed.
- mypy must not be pointed at several `src` directories without mapping them. We type-check
  **per package**: from the package directory with `explicit_package_bases = true` and
  `mypy_path = "src"`, checking `src` and `tests` (implemented in M0-3 by `scripts/typecheck.py`).
  This also avoids clashes between identically named test modules of different packages.
- Files placed in the member globs (e.g. `packages/README.md`) are ignored by uv.
