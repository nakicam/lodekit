# Continuous integration

All checks live in [`.github/workflows/ci.yml`](https://github.com/nakicam/lodekit/blob/main/.github/workflows/ci.yml). It runs on pull
requests, pushes to `main`, merge-queue groups, and on demand (`workflow_dispatch`). Workflow
permissions default to `contents: read`.

## Per-package scoping

The `changes` job runs `scripts/dev.py affected --base <PR base SHA>`:

- A file changed under `packages/<name>/` or `examples/<name>/` marks that member as affected,
  and so are all members that depend on it in the workspace (transitively).
- Changes to workspace-wide files mark **every** member as affected. These are the root
  `pyproject.toml`, `uv.lock`, `.python-version`, `.github/workflows/`, `.github/actions/`,
  `scripts/` and the root `LICENSE` and `NOTICE`.
- Pushes to `main` and manual runs use `--all`.

Typecheck, test and isolation jobs receive the resulting JSON list (`--members-json`). Repository
tooling (`scripts/`, `tests/`) is always checked.

Reproduce it locally:

```console
uv run python scripts/dev.py affected --base origin/main
uv run python scripts/dev.py test --members-json '["lodekit-common"]'
```

## Jobs

| Job | What it checks |
|---|---|
| `changes` | Computes affected members and publishable packages. |
| `lint` | `uv lock --check`, `ruff check`, `ruff format --check`, per-package `LICENSE`/`NOTICE` copies, namespace guard (`scripts/check_namespace.py`: dotted `module-name = "lodekit.<pkg>"`, no `module-name = "lodekit"`, no `namespace = true`), actionlint. The isolation job runs the guard again on the built wheels (no top-level `lodekit/__init__.py`). |
| `typecheck` | `mypy --strict` per affected member (namespace-safe, see [toolchain](toolchain.md)) on Python 3.11. |
| `ty` | Astral `ty`, **informational only** (`continue-on-error`). |
| `test` | pytest (`-m "not live"`) on Ubuntu × Python 3.11–3.14, plus Windows and macOS on 3.12. |
| `isolation` | For each affected publishable package, builds the wheel and installs it into a clean venv with no workspace and no editable installs. It also adds wheels of sibling packages as `--find-links`, so only *declared* dependencies resolve. It asserts that `lodekit` is a namespace package and that the module is imported from `site-packages`, then runs the package's unit and contract tests against the installed wheel. |
| `lowest-direct` | `uv sync --resolution lowest-direct` on Python 3.11 plus the tests; this keeps declared lower bounds honest. |
| `licenses` | Installs only runtime dependencies (`--no-dev`) and runs `scripts/check_licenses.py` against the [ADR-000](../decisions/0000-license-apache-2.0.md) allow-list (`[tool.lodekit.license-check]` in the root `pyproject.toml`). The report goes to the job summary. |
| `dependency-tree` | `uv tree --no-dev` and the number of third-party runtime distributions go to the job summary and an artifact. Watched transitive dependencies (`langsmith`, `langgraph-sdk`) are flagged. |
| `docs` | `mkdocs build --strict` for the documentation site (see [documentation](docs.md)). |
| `secrets` | gitleaks over the full history. |
| `ci-success` | Aggregator. Fails if any job above failed or was cancelled; skipped jobs (no affected package) count as success. |

### Licence exceptions

A dependency outside the allow-list fails the `licenses` job. To accept it anyway, add an entry
with a justification and a link to the ADR-000 discussion:

```toml
[tool.lodekit.license-check.exceptions]
"some-dist" = "MPL-2.0, used unmodified as a runtime dependency; see #123"
```

## Required status check

Branch protection on `main` should require **only** the `CI success` check. Requiring individual
matrix jobs breaks whenever the matrix changes, or when a job is skipped because no package is
affected. Settings → Branches → `main`:

1. Require a pull request before merging (1 approval, dismiss stale approvals).
2. Require status checks to pass: `CI success`; require branches to be up to date.
3. Require signed-off commits (DCO) and linear history; block force pushes and deletions.

Equivalent API call (admin only):

```console
gh api -X PUT repos/nakicam/lodekit/branches/main/protection --input protection.json
```

with `protection.json`:

```json
{
  "required_status_checks": {"strict": true, "contexts": ["CI success"]},
  "enforce_admins": false,
  "required_pull_request_reviews": {"required_approving_review_count": 1, "dismiss_stale_reviews": true},
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```

The `examples-smoke` job ([examples conventions](https://github.com/nakicam/lodekit/blob/main/examples/README.md)) becomes a second
required check once the first example exists.
