# Examples

Runnable examples that show what lodekit packages do from a user's point of view. Each example
also serves as a smoke test of the **released artefacts**. CI builds the wheels, installs them
into a clean virtual environment together with only the example's declared dependencies, and runs
the example (`examples-smoke`).

> Status: pre-alpha. Package and example names may still change.

## Conventions

Every example **must**:

1. **Live in its own folder** `examples/<name>/`, with a short, lower-case, hyphenated name, e.g.
   `examples/hello-agent/`. Each folder is a uv workspace member.
2. **Run with one command** after installing, e.g. `python main.py`. There are no setup scripts
   and no manual steps.
3. **Run offline by default.** It needs no network, no API key and no Docker, unless the README
   states otherwise up front. CI points `HTTP(S)_PROXY` to an unreachable address and removes
   provider API keys.
4. **Use a fake model for agent and RAG examples** by default (e.g.
   `lodekit.agents.testing.FakeToolCallingModel`). A real provider is optional and is selected via
   an environment variable or a `--model provider:model` flag. Keys only ever come from
   environment variables.
5. **Be deterministic.** It uses fixed seeds and prints real output. CI asserts the key result
   line, so a README's "Expected output" can never drift from reality.
6. **Follow the [README template](README_TEMPLATE.md)**, including the "Data" section, the
   pre-alpha notice and the trademark footer (only when DuckDB is used; never the DuckDB logo).
7. **Declare its data licence** in its README *and* in [DATA_LICENSES.md](DATA_LICENSES.md). This
   is mandatory, even for synthetic data.
8. **Declare dependencies by package name** with compatible ranges. Inside the workspace they
   resolve via `[tool.uv.sources]`; in `examples-smoke` they resolve from the built wheels.
9. Contain no secrets, no company data and no real personal data.
10. Copy-paste in bash **and** PowerShell. When the commands differ, show both.

## Layout

```text
examples/<name>/
├── README.md        # from README_TEMPLATE.md
├── pyproject.toml   # dependencies + [tool.lodekit.example]
├── main.py          # the one entry point
└── tests/           # optional extra tests (pytest marker: e2e)
```

`pyproject.toml`:

```toml
[project]
name = "example-<name>"
version = "0"
requires-python = ">=3.11"
dependencies = ["lodekit-common>=0.1,<0.2"]

[tool.uv.sources]
lodekit-common = { workspace = true }

[tool.lodekit.example]
run = ["python", "main.py"]   # executed in a copy of the example folder
expect = ["run_id="]          # substrings that must appear in stdout
timeout = 300                 # seconds
```

Examples have no `[build-system]`. They are never published, and only their dependencies are
installed.

## Running examples

In the workspace (uses your local sources):

```console
uv run --package example-<name> python examples/<name>/main.py
```

Like a user would, from built wheels in a clean venv (this is what CI runs):

```console
uv run python scripts/examples_smoke.py                 # all examples
uv run python scripts/examples_smoke.py example-<name>  # one example
```

## `examples-smoke` in CI

The `examples-smoke` job in [`ci.yml`](../.github/workflows/ci.yml) runs on Ubuntu and Windows.

- It builds wheels for every publishable package.
- For each affected example it creates a fresh venv and installs only the wheels the example
  depends on (transitively), plus its declared third-party dependencies.
- It runs the example from a copy of its folder outside the repository, and asserts the exit code
  and the `expect` lines.

The job is part of the aggregated `CI success` check, so it is **required on `main`** as soon as
the first example exists. While there are no examples, it passes trivially.

## Data

The shared dataset for M1, M2 and M5 is the synthetic, CC0 **retail dataset**; see the
[EX-1 specification](../docs/examples/synthetic-retail-dataset.md). It is generated at runtime
with a fixed seed, so expected answers are exact.

Datasets with restrictive terms (Open-Meteo, TPC-H, NYC TLC trip data) are **only downloaded at
runtime and never committed**. See [DATA_LICENSES.md](DATA_LICENSES.md).
