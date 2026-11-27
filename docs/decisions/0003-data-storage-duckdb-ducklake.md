---
status: proposed
date: 2026-11-27
decision-makers: Naki (maintainer), lead
---

# ADR-003: Data storage: embedded DuckDB + DuckLake, storage separated from runtime

Status **Proposed**. This becomes final after spike S3 (storage mini benchmark), which is still
running.

## Context and problem statement

- DuckDB 2.0 LTS is the default engine.
- DuckLake 1.0 (stable since 04/2026) provides transactional tables and snapshots on Parquet.
- Embedded DuckDB allows only **one writing process**.
- Catalog backends:
  - DuckDB: one writer;
  - SQLite: several local processes, one writer with retry;
  - PostgreSQL: multi-user;
  - Quack.

Agents and pipelines may run concurrently. How should lodekit packages store and access data?

## Considered options

- Embedded DuckDB + DuckLake with storage profiles
- Plain DuckDB files without DuckLake
- Iceberg or Delta
- A DuckDB catalog as the default

## Decision outcome (proposed)

1. **Engine.** DuckDB is the default engine but not mandatory. Packages access storage only through
   a small `StorageProfile` contract (catalog URI, data path, mode `read_write | read_only`), never
   through hard-coded paths.
2. **Table format.** DuckLake is the table format for persisted data products.
3. **Profiles:**
   - `local` is a SQLite catalog plus a local Parquet path. It is the default, also in CI.
   - `team` is a PostgreSQL catalog plus S3-compatible object storage.
4. **Single-writer rule.** Only pipelines (`lodekit-flow`) write. Agents (`lodekit-agents`) and
   quality checks (`lodekit-quality`) open **read-only** connections.
5. **Secrets.** S3 keys and Postgres passwords come only from the environment or a secret store.
   They are never placed in config files, prompts or SQL.
6. **No DuckDB wrappers** (decision D1b). lodekit configures and uses DuckDB, DuckLake, dlt and
   dbt-duckdb as they are. It does not wrap the DuckDB API.

### Consequences

- Good: a local zero-ops setup that scales to a team profile without code changes.
- Bad: the SQLite profile has write contention, which pipelines handle by serializing writes.
- Open: Windows behaviour and S3-compatible storage must be validated in spike S3.

### Confirmation

- Spike S3 runs two writers on SQLite and Postgres catalogs, an agent reading during a dlt load,
  MinIO as the data path, and a Windows check.
- Contract tests check that read-only profiles really open read-only connections.

## Pros and cons of the options

- **Plain DuckDB files without DuckLake.** No snapshots and weak concurrency.
- **Iceberg or Delta.** More complex and less DuckDB-native.
- **A DuckDB catalog as the default.** A single writer would block agents.
