# Data licences for examples

The Apache-2.0 licence of the lodekit code does **not** cover data. Every dataset that an example
generates, downloads or commits must be listed here **before** the example is merged. CI and
review check that each example's README "Data" section matches this table.

## Rules

1. **Prefer synthetic data** that is generated at runtime with a fixed seed and dedicated to the
   public domain (CC0-1.0).
2. **Committed snapshots** are allowed only for datasets whose licence permits redistribution
   (e.g. CC0, CC-BY with attribution). Keep them small (≤ 10 MB) and include the attribution.
3. **Runtime download only, never committed:** datasets whose terms restrict redistribution or
   bulk copies. These are:
   - **Open-Meteo:** CC-BY 4.0 data via an API with usage terms. Download at runtime with
     attribution. The example must not be required to run offline in CI, or it must use a
     synthetic fallback.
   - **TPC-H:** generate it locally with the DuckDB `tpch` extension (`CALL dbgen(sf => …)`). The
     TPC EULA forbids publishing the generated data and benchmark results as "TPC-H results".
   - **NYC TLC trip records:** download at runtime from the official source and observe the
     source's terms of use.
4. **No personal or company data.** Fictional names must be obviously fictional.
5. Attribution text required by a licence goes into the example README and into this table.

## Register

| Dataset | Used by | Source | Licence | Committed? | Attribution |
|---|---|---|---|---|---|
| Synthetic retail dataset ("Northbridge Supply", fictional) | EX-2, EX-3, analyst-mini (planned) | Generated at runtime by `lodekit-flow` (DF-2), seed 42; [specification](../docs/examples/synthetic-retail-dataset.md) | CC0-1.0 | No (generated) | none required |

*Add a row per dataset. "Used by" lists the example folders.*
