# lodekit

**Open-source data & AI toolkit for local-first analytics.**

> **Status: pre-alpha.** Nothing is released yet. APIs, package names and layout may change
> without notice until the first `0.1` releases.

## Vision

lodekit is a set of small, loosely coupled Python packages that take you from raw data to
trustworthy answers on your own machine:

- load and transform data into an embedded analytical store,
- check its quality against explicit data contracts,
- let agents answer questions over the curated data, read-only and with controlled state.

Every package is installable on its own, released independently and licensed under Apache-2.0.
lodekit provides thin, typed wrappers over established open-source tools (dlt, dbt, LangGraph,
Pydantic and more) with one shared CLI and shared contracts. DuckDB and DuckLake are used directly
as the storage engine, without a wrapper.

## Packages

| Package | Import | Purpose | Milestone | Status |
|---|---|---|---|---|
| `lodekit-common` | `lodekit.common` | Shared contracts (`RunContext`, data and quality descriptors) | M0 / M1 | planned |
| `lodekit-flow` | `lodekit.flow` | Pipelines: dlt ingest and dbt transforms on DuckLake | M1 | planned |
| `lodekit-quality` | `lodekit.quality` | Engine-neutral quality checks and data contracts | M1 | planned |
| `lodekit-agents` | `lodekit.agents` | Agents and teams on LangGraph with tool registry, state guards and limits | M2 | planned |

All packages share the implicit namespace `lodekit.*` (PEP 420). See the
[roadmap](docs/roadmap.md) and the [architecture decisions](docs/decisions/).

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and our
[Code of Conduct](CODE_OF_CONDUCT.md). Report security issues privately as described in
[SECURITY.md](SECURITY.md).

## License

Apache License 2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE). Example datasets may be under
different licences, see `examples/DATA_LICENSES.md`.

---

<sub>lodekit is built on DuckDB. DuckDB is a trademark of the DuckDB Foundation. lodekit is
independent and not affiliated with or endorsed by the DuckDB Foundation.</sub>
