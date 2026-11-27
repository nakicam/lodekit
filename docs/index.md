# lodekit

lodekit is a set of composable, independently installable Python packages for data and AI
workflows, built on DuckDB. Every capability ships as its own `lodekit-*` distribution in the
shared `lodekit.*` namespace, so you install only what you need.

lodekit provides thin, typed wrappers over established open-source tools (dlt, dbt, LangGraph,
Pydantic and more) with one shared CLI and shared contracts. DuckDB and DuckLake are used directly
as the storage engine, without a wrapper.

!!! warning "Pre-alpha"
    lodekit is in milestone M0 (monorepo foundation). APIs and package names may still change, and
    nothing has been published to PyPI yet.

## Packages (planned for the first 90 days)

| Distribution | Import | Purpose | Milestone |
|---|---|---|---|
| `lodekit-common` | `lodekit.common` | Shared contracts such as `RunContext`, data and quality contracts | M0 / M1 |
| `lodekit-flow` | `lodekit.flow` | Pipelines with dlt and dbt-duckdb on DuckLake | M1 |
| `lodekit-quality` | `lodekit.quality` | Engine-neutral data quality checks and data contracts | M1 |
| `lodekit-agents` | `lodekit.agents` | Agent composition layer on LangChain `create_agent` and LangGraph | M2 |

## Where to go next

- [Roadmap](roadmap.md): milestones M0–M5.
- [Architecture decisions](decisions/index.md): the ADRs behind the design.
- [Development](development/toolchain.md): how to work on the monorepo.

---

<small>Built on DuckDB. DuckDB is a trademark of the DuckDB Foundation. lodekit is independent and
not affiliated with or endorsed by the DuckDB Foundation.</small>
