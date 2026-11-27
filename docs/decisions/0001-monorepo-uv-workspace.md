---
status: proposed
date: 2026-11-27
decision-makers: Naki (maintainer), lead
---

# ADR-001: Monorepo with uv workspace and independent package releases

Status **Proposed**. It is accepted once the M0 foundation has proved the release flow. The
namespace and mypy part has already been verified in
[spike 0001](../spikes/0001-namespace-packages-mypy.md).

## Context and problem statement

lodekit consists of loosely coupled capabilities, and each one must be installable on its own. The
project is developed part-time by one maintainer plus agent sessions. The shared contracts package
`lodekit-common` must evolve in lockstep with its consumers. How should the code be organized,
built, checked and released?

## Decision drivers

- Each package must install on its own, with independent versions.
- Contracts change atomically with their consumers.
- One maintainer means one set of tooling and one CI.
- Python ≥ 3.11, a PEP 420 namespace `lodekit.*`, and a CI matrix over 3.11–3.14.

## Considered options

- One monorepo with a uv workspace and independent releases
- A polyrepo per package
- Pants or Bazel
- Hatch without a workspace lock
- One distribution with extras only

## Decision outcome

Chosen option: **one public monorepo with a uv workspace**. Each capability is a separate Python
distribution under `packages/`, packages are created only when the current milestone needs them,
and everything shares one `uv.lock`.

| Area | Choice |
|---|---|
| Workspace and build | uv workspace + `uv_build`, pinned with an upper bound. Fall back to hatchling only if a build hook is needed. |
| Namespace | PEP 420 `lodekit.*` via a dotted `module-name`. There is no `lodekit/__init__.py` in any distribution. |
| Lint and format | ruff (check + format) |
| Types | `mypy --strict` as the CI gate, run per package (`explicit_package_bases`). `ty` runs as a non-blocking job until 1.0. |
| Tests | pytest with markers `unit`, `contract`, `integration`, `e2e` and `live`. Python 3.11–3.14 matrix plus a `lowest-direct` job and per-package isolation jobs. |
| Release | release-please in manifest mode with `separate-pull-requests: true`. Tags are `<pkg>-v<semver>`, e.g. `lodekit-common-v0.1.0`. |
| Publish | PyPI Trusted Publishing (OIDC). One `release.yml` with a protected environment and attestations; TestPyPI first. |
| Hooks | pre-commit: ruff, ruff-format, mypy, `uv lock --check`, Conventional Commits, basic fixers |

The documented developer workflow lives in [toolchain](../development/toolchain.md),
[package layout](../development/package-layout.md) and [CI](../development/ci.md).

### Consequences

- Good: changes across contracts and their consumers are atomic, with one CI and consistent tooling.
- Good: users still install only the packages they need.
- Bad: CI needs path filters (affected members including dependents) and isolation jobs to prove
  each package installs on its own.
- Bad: release-please neither updates `uv.lock` nor bumps inter-member pins. Mitigations:
  - a post-release `uv lock` step;
  - compatible ranges such as `lodekit-common>=0.1,<1`;
  - no cascade releases, so a breaking change in common is released manually.
- Bad: uv is 0.x, so CI pins its version.
- Bad: a PyPI pending publisher does not reserve the project name. Names and publishers are
  registered only after maintainer approval.

### Confirmation

- The CI workflow: lint, typecheck, test, isolation, lowest-direct and licences.
- A TestPyPI dry run of the release flow (M0-5).

## Pros and cons of the options

- **Polyrepo per package.** Rejected: cross-package changes and contract evolution become
  multi-PR work, and CI and tooling are duplicated N times.
- **Pants or Bazel.** Rejected as too heavy for about a dozen pure-Python packages and this team
  size.
- **Hatch without a workspace lock.** Rejected because there is no single lockfile.
- **One distribution with extras only.** Rejected because it blurs component boundaries and forces a
  single release cadence.

## More information

- uv workspaces: <https://docs.astral.sh/uv/concepts/projects/workspaces/>
- uv_build namespace packages: <https://docs.astral.sh/uv/concepts/build-backend/#namespace-packages>
- release-please manifest releaser: <https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md>
- PyPI Trusted Publishing: <https://docs.pypi.org/trusted-publishers/>
- Open points:
  - whether the root should become the meta package `lodekit`;
  - the setup effort for one pending publisher per package.
