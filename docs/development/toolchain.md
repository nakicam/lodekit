# Toolchain and tests

One binding toolchain for all packages, configured once in the root `pyproject.toml`.

| Tool | Purpose | Command |
|---|---|---|
| ruff | lint + format (shared root config) | `uv run ruff check .` / `uv run ruff format .` |
| mypy `--strict` + pydantic plugin | **binding** type checker, run per package | `uv run python scripts/dev.py typecheck [MEMBER ...]` |
| ty | informational only (CI job is non-blocking until ty 1.0) | `uvx ty check` |
| pytest (+ pytest-asyncio, pytest-cov) | tests, run per package with coverage | `uv run python scripts/dev.py test [MEMBER ...]` |
| pre-commit | runs all of the above plus basic fixers, `uv lock --check` and the Conventional Commits check | `uv run pre-commit run --all-files` |

mypy runs once per workspace member from the member directory because several `src` trees share
the PEP 420 namespace `lodekit` (see the [namespace spike](../spikes/0001-namespace-packages-mypy.md)).

## Test levels and markers

Markers are declared in the root config and `--strict-markers` rejects unknown ones.
Every test carries exactly one level marker.

| Marker | Location | Content | Rule |
|---|---|---|---|
| `unit` | `packages/*/tests/unit` | logic per module | no network, no real LLMs (fake models) |
| `contract` | `packages/*/tests/contract` | public API (`__all__`) and JSON schema snapshots | fails on unintended API changes |
| `integration` | `packages/*/tests/integration` | real local engines with temporary files | runs in PR CI |
| `e2e` | `tests/e2e` | cross-package flows with fake models | runs in PR CI |
| `live` | anywhere | real external services or LLM providers | **never in PR CI**; manual or nightly only |

`live` tests are deselected by default (`-m "not live"` in `addopts`). Run them explicitly with
`uv run pytest -m live`.

Further defaults: `--import-mode=importlib` (test modules of different packages may share names),
warnings are errors, `xfail` is strict and asyncio tests run in auto mode.
