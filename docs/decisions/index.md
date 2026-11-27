# Architecture decision records

Significant architecture decisions are recorded as ADRs in this directory. The format follows
[MADR 4](https://adr.github.io/madr/), and new ADRs start from [the template](template.md).

| ADR | Title | Status |
|---|---|---|
| [ADR-000](0000-license-apache-2.0.md) | Project licence: Apache-2.0 | Accepted |
| [ADR-001](0001-monorepo-uv-workspace.md) | Monorepo with uv workspace and independent package releases | Proposed |
| [ADR-002](0002-agent-runtime-langgraph.md) | Agent runtime: LangGraph as the only runtime, lodekit-agents as the DX layer | Accepted |
| [ADR-003](0003-data-storage-duckdb-ducklake.md) | Data storage: embedded DuckDB + DuckLake, storage separated from runtime | Proposed |

Expected later: ADR-004 versioning of `lodekit-common` contracts, ADR-005 orchestrator, ADR-006
quality engine.

## Process

1. Copy `template.md` to `NNNN-short-title.md`, using the next free number.
2. Open a PR with status **Proposed**. Discussion happens in the PR.
3. The maintainer accepts or rejects it. Set the status and date and add a row to the table above.
4. Accepted ADRs are not rewritten. A new ADR supersedes the old one, and both are cross-linked.
   Small factual corrections and amendments are added as dated notes.
