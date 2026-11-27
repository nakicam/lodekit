# Roadmap

lodekit is built in milestones. A package is only added to the repository when a milestone needs
it, and it is only released when the release gate is met:

- CI is green;
- the acceptance criteria are met;
- the "Fresh Eyes" user check passes;
- the maintainer approves.

Everything stays `0.x` until M5.

| Milestone | Weeks | Goal | Packages | Gate |
|---|---|---|---|---|
| **M0** Monorepo foundation | W1–3 | Installable skeleton with CI, docs, ADRs and a release pipeline | `lodekit-common` 0.1 (TestPyPI) | G2 |
| **M1** Data foundation | W4–8 | One offline command: source → DuckLake → quality report | `lodekit-common` 0.2, `lodekit-flow` 0.1, `lodekit-quality` 0.1 | G3 |
| **M2** Agent core | W9–13 | Agent with tools and controlled state; analyst-mini reads M1 data read-only | `lodekit-agents` 0.1 | G4 |
| **M3** AI, evaluation and tracing | after day 90 | RAG with evaluation and tracing ("ask the docs") | to be planned | – |
| **M4** Serving | after day 90 | Serve agents over REST and MCP with authentication | to be planned | – |
| **M5** End-to-end flagship | after day 90 | Analyst end-to-end with a dashboard; path towards 1.0 | to be planned | – |

M3–M5 indicate direction only and are not a commitment. They are planned in detail after M2.

## M0: Monorepo foundation

- [ ] Governance files: licence, notice, contributing, code of conduct, security policy, templates
  ([#1](https://github.com/nakicam/lodekit/issues/1))
- [ ] uv workspace with the PEP 420 namespace `lodekit.*` ([#2](https://github.com/nakicam/lodekit/issues/2))
- [ ] ruff, mypy --strict, pytest and pre-commit ([#3](https://github.com/nakicam/lodekit/issues/3))
- [ ] CI with a per-package matrix, isolation, lowest-direct, licence check and dependency-tree
  report ([#4](https://github.com/nakicam/lodekit/issues/4))
- [ ] Docs site and ADRs ([#6](https://github.com/nakicam/lodekit/issues/6))
- [ ] Release pipeline: release-please plus TestPyPI Trusted Publishing ([#5](https://github.com/nakicam/lodekit/issues/5))
- [ ] Security baseline: CodeQL, Dependabot, secret scanning ([#7](https://github.com/nakicam/lodekit/issues/7))
- [ ] Examples conventions and `examples-smoke` ([#8](https://github.com/nakicam/lodekit/issues/8))
- [ ] `lodekit-common` 0.1 with `RunContext` ([#9](https://github.com/nakicam/lodekit/issues/9))

**Done when:** CI is green, `lodekit-common` 0.1.0 is on TestPyPI, and user check G2 passes.

## M1: Data foundation

- [ ] Contracts `DataSource`, `DataAsset`, `StorageProfile`, `QualityCheck`, `QualityResult`, and a
  contract versioning policy (ADR-004).
- [ ] `lodekit-flow`:
  - storage profiles;
  - the synthetic retail generator (EX-1), ingested via dlt into DuckLake;
  - a dbt-duckdb transform;
  - a pipeline runner CLI.
- [ ] `lodekit-quality`:
  - an engine-neutral check API;
  - baseline checks and a dbt-test adapter;
  - data contract validation;
  - a quality report.

**Done when:** one command loads the example source via dlt into DuckLake, transforms it with dbt,
checks it with lodekit-quality and writes a report plus `DataAsset.quality_status`. This runs
offline in CI as an e2e test.

## M2: Agent core

- [ ] `lodekit-agents` with:
  - `ToolRegistry` and policy;
  - `State` with write guards and limits as middleware;
  - `Agent` on `create_agent`;
  - `ask()` / `aask()` with `Result`;
  - a sequential `Team`.
- [ ] Examples `hello-agent`, `registry-and-state` and `analyst-mini`.

**Done when:** `pip install lodekit-agents` works without DuckDB, and analyst-mini answers a
question about the M1 data with a fake model in CI and with a provider of your choice locally.
