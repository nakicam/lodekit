# Contributing to lodekit

Thanks for your interest in lodekit! This document explains how to set up a development
environment and how we work.

## Ground rules

- Be kind. All participation is governed by our [Code of Conduct](CODE_OF_CONDUCT.md).
- Never commit secrets, credentials, personal data or proprietary/company data.
- Every change goes through a pull request. Only the maintainer merges.
- Report vulnerabilities privately, see [SECURITY.md](SECURITY.md).

## Development setup

lodekit is a monorepo managed as a [uv](https://docs.astral.sh/uv/) workspace.

1. Install uv (see the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)).
2. Clone the repository and sync the workspace (installs Python 3.12 if needed, all workspace
   packages in editable mode and the dev tools):

   ```bash
   git clone https://github.com/nakicam/lodekit.git
   cd lodekit
   uv sync --all-packages
   ```

3. Install the git hooks:

   ```bash
   uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
   ```

4. Run the checks locally:

   ```bash
   uv run pre-commit run --all-files        # everything below plus fixers
   uv run ruff check .
   uv run ruff format --check .
   uv run python scripts/dev.py typecheck   # mypy --strict, per package
   uv run python scripts/dev.py test        # pytest, per package, with coverage
   ```

Both helpers accept member names, e.g. `scripts/dev.py test lodekit-common`. See
[Toolchain and tests](docs/development/toolchain.md) for markers and test levels.

## Repository layout

```text
packages/<name>/          one Python distribution per package (src layout, PEP 420 namespace lodekit.*)
examples/<name>/          runnable examples, each its own workspace member
docs/                     documentation site and architecture decision records (docs/decisions/)
```

## Commit messages: Conventional Commits

We use [Conventional Commits](https://www.conventionalcommits.org/). Release notes and
version bumps are generated from them, so the format matters.

```text
<type>(<scope>): <short summary>
```

- **type:** `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.
  Mark breaking changes with `!` (e.g. `feat(common)!: ...`) or a `BREAKING CHANGE:` footer.
- **scope:** the package without the `lodekit-` prefix (`common`, `flow`, `quality`, `agents`),
  or a repository area (`repo`, `ci`, `docs`, `examples`, `release`, `deps`).

Examples:

```text
feat(common): add RunContext model
fix(agents): raise LimitExceeded with partial state
ci(repo): add lowest-direct resolution job
```

## Developer Certificate of Origin (DCO)

We use the [Developer Certificate of Origin](https://developercertificate.org/) instead of a CLA.
Every commit must carry a `Signed-off-by` line matching the commit author. Add it with `-s`:

```bash
git commit -s -m "feat(common): add RunContext model"
```

By signing off you certify that you wrote the change or otherwise have the right to submit it
under the Apache-2.0 licence. Forgot it? Fix the last commit with `git commit --amend -s`, or a
whole branch with `git rebase --signoff main`.

## Pull requests

- One issue (or a small, coherent group) per pull request; reference it with `Closes #<n>`.
- Fill in the pull request template, including the release-gate checklist.
- Keep CI green: lint, `mypy --strict`, tests on the Python matrix, contract tests,
  `examples-smoke`, licence and secret scans.
- New dependencies of core packages must be MIT, BSD, Apache-2.0, ISC or PSF licensed
  (see [ADR-000](docs/decisions/0000-license-apache-2.0.md)).
- If you build a feature, also add or update its minimal example.

## Naming and trademarks

DuckDB is a trademark of the DuckDB Foundation. Refer to it only descriptively
("built on DuckDB", "for DuckDB"). Do not use the DuckDB logo or "Duck"-derived names for
lodekit components.
