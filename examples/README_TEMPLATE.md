# Example README Template

> **Status:** Draft v0.1 · **Owner:** examples maintainers · **Date:** 2026-11-27
> Every folder under `examples/` uses this template (EX-0). Replace `<…>` placeholders and delete these instructions and all `<!-- … -->` comments. Keep the README short: a new user should get from zero to output in one screen.

---

# <Example title – what you build, in plain words>

<!-- One sentence. Example: "Ask a question in plain English and get the unusual region from last quarter's sales data." -->
<One-sentence outcome.>

| | |
|---|---|
| **Milestone** | <M1 / M2 / …> |
| **Packages** | `<pkg>`, `<pkg>` |
| **Time to run** | < <N> min from a clean environment |
| **Needs network / API key** | No (offline, fake model). Optional: a real model, see [Use a real model](#use-a-real-model) |
| **Data** | <dataset name> – <licence> (see [Data](#data)) |
| **Status** | pre-alpha · names are working titles |

## What you'll build

<!-- 3–5 bullets, user perspective, no internals. -->
- <bullet>
- <bullet>

<!-- Optional: small Mermaid diagram, ≤ 8 nodes, short labels. -->
```mermaid
flowchart LR
  A[<Source>] --> B[<Step>] --> C[<Result>]
```

## Prerequisites

- Python 3.11–3.14
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`
<!-- List anything else explicitly, e.g. Docker for M4/M5. Nothing hidden. -->

## Run it

<!-- Exactly one command after install. Provide bash and PowerShell only if they differ. -->

```bash
uv run --with <pkg> python main.py
```

or with pip:

```bash
python -m venv .venv
# bash: source .venv/bin/activate    PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

### Expected output

<!-- Paste the real, deterministic output (shortened with "…" if needed). CI asserts the key line. -->
```text
<expected output>
```

**Key result:** <the one fact the user should see, e.g. "North-East revenue −24 % QoQ">.

## What just happened

<!-- 3–6 numbered steps mapping output to concepts. Link to package docs instead of explaining APIs. -->
1. <step> – see [`<pkg>` docs](<link>)
2. <step>

## Use a real model

<!-- Only for agent/RAG examples. Never put keys in files; env vars only. -->
```bash
export <PROVIDER>_API_KEY=...        # PowerShell: $env:<PROVIDER>_API_KEY="..."
python main.py --model <provider:model>
```
Results can differ slightly from the fake-model output; the key result should be the same.

## Try next

- <variation the user can make in 1 minute, e.g. "change the question in `main.py`">
- <link to next example / tutorial>

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: <x>` | install the extra: `pip install "<pkg>[<extra>]"` |
| <symptom> | <fix> |

## Data

<Dataset name>, <synthetic | source URL>, licence **<CC0-1.0 | …>**. <Attribution text if required.>
See [`examples/DATA_LICENSES.md`](../DATA_LICENSES.md).

---

<sub>Part of **lodekit**, licensed under Apache-2.0. Built on DuckDB. DuckDB is a trademark of the DuckDB Foundation; this project is independent and not affiliated with or endorsed by the DuckDB Foundation.</sub>
<!-- Keep this footer only if the example actually uses DuckDB. Never use the DuckDB logo. -->

---

## Template checklist (delete before merging)

- [ ] One command after install; runs offline with the fake model, no API key
- [ ] Expected output is real and matches what CI asserts
- [ ] Time to run measured from a clean venv on Windows and Linux
- [ ] All code blocks copy-paste on bash **and** PowerShell
- [ ] No secrets, no company data, no dead links
- [ ] Data licence stated here and in `DATA_LICENSES.md`
- [ ] No DuckDB logo; DuckDB only as subordinate text attribution with trademark notice
- [ ] Working-title / pre-alpha notice present
- [ ] `pyproject.toml` declares deps by package name (resolved via `[tool.uv.sources]` in the workspace)
