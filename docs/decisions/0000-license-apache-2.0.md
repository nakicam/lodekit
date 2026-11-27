---
status: accepted
date: 2026-11-27
decision-makers: Naki (maintainer)
---

# ADR-000: Project licence: Apache-2.0

Decision D2, accepted 2026-11-27, based on spike S1. Not legal advice.

## Context and problem statement

lodekit is a public, community-oriented Python monorepo with independently released `lodekit-*`
packages. Which licence should the packages use, and which licences may their dependencies have?

Core dependency licences per PyPI metadata (retrieved 2026-11-27):

- **MIT:** duckdb, langchain-core / langchain / langgraph, pydantic, fastapi, mcp, the langfuse SDK.
- **Apache-2.0:** dlt, dbt-core, dbt-duckdb, dagster, prefect, opentelemetry, openlineage-python,
  pyarrow, ragas, deepeval, great-expectations, streamlit, acryl-datahub.
- **Problem cases:**
  - openmetadata-ingestion uses the "Collate Community License Agreement v1.0", which is not
    OSI-approved.
  - soda-core is listed as "Proprietary" in its PyPI metadata.
  - Metabase is AGPL-3.0 (assumption).

## Decision drivers

- Adoption by companies building AI and data tooling, which needs patent clarity.
- Alignment with the surrounding data stack.
- Low friction for contributors.

## Considered options

- Apache-2.0
- MIT
- BSD-3-Clause
- MPL-2.0
- AGPL, BSL or fair-source licences

## Decision outcome

Chosen option: **Apache License 2.0** for all packages in the monorepo.

- It has an explicit patent grant and a patent retaliation clause.
- It is the same licence as most of the data stack (dlt, dbt, Dagster, Prefect, OpenTelemetry,
  Arrow).
- Apache-2.0 code may depend on MIT and Apache-2.0 packages, which is standard practice in the
  Python ecosystem.

### Consequences and implementation rules

1. **Licence files.** The root `LICENSE` contains the full Apache-2.0 text. `NOTICE` contains the
   copyright line. Each package declares `license = "Apache-2.0"` (a PEP 639 SPDX expression) and
   `license-files = ["LICENSE", "NOTICE"]`. Packages keep byte-identical copies of both files,
   checked by `scripts/dev.py check-license-files`; see
   [package layout](../development/package-layout.md).
2. **DCO, not a CLA.** Contributors sign off their commits (`git commit -s`). Apache-2.0 §5 already
   covers inbound contributions.
3. **Dependency licence policy:**
   - Core (runtime) dependencies may only use MIT, BSD, Apache-2.0, ISC or PSF licences.
   - Weak copyleft (MPL, LGPL) is allowed only as an optional extra.
   - GPL, AGPL, BSL, ELv2, "Proprietary" and other non-OSI licences are never core dependencies.
     They may at most be an optional extra with an explicit README note, or a separate service.
     They are never linked or vendored.
   - CI enforces the policy with `scripts/check_licenses.py` in the `licenses` job (see
     [CI](../development/ci.md)).
4. **Trademark.** The licence grants no trademark rights (Apache-2.0 §6). The README footer says:
   "DuckDB is a trademark of the DuckDB Foundation. lodekit is independent and not affiliated with
   or endorsed by the DuckDB Foundation." lodekit does not use the DuckDB logo.
5. **Example data.** Data in examples is not covered by the code licence. It is listed in
   `examples/DATA_LICENSES.md`.

### Confirmation

- The `licenses` CI job and `check-license-files` in the `lint` job.
- PR review against the DoD checklist.

## Pros and cons of the options

- **MIT.** Simple, and matches DuckDB and LangChain, but has no patent clause.
- **BSD-3-Clause.** Similar to MIT, also without a patent clause.
- **MPL-2.0.** File-level copyleft, which causes friction in Python.
- **AGPL, BSL and fair-source licences.** These contradict the goal of community packages.
