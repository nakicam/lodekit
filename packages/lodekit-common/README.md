# lodekit-common

Shared foundations for [lodekit](https://github.com/nakicam/lodekit) packages. Version 0.1
provides `RunContext`, the correlation context that links runs of lodekit components (pipelines,
quality checks, agents) to each other.

> **Status: pre-alpha.** The API may change in any 0.x minor release.

## Install

```console
pip install lodekit-common
```

## Usage

```python
from lodekit.common import RunContext

pipeline = RunContext(component="lodekit-flow", tags=("nightly",))
check = pipeline.child("lodekit-quality")

assert check.parent_run_id == pipeline.run_id
print(check.model_dump_json())
```

`RunContext` is an immutable Pydantic v2 model with these fields:

| Field | Type | Default |
|---|---|---|
| `run_id` | UUID | random (`uuid4`) |
| `parent_run_id` | UUID or `None` | `None` |
| `component` | string matching `^[a-z][a-z0-9_.-]*$` | required |
| `started_at` | timezone-aware datetime | now, UTC |
| `tags` | tuple of strings (deduplicated, order kept) | `()` |

The JSON schema is part of the public contract:

```console
python -m lodekit.common > run-context.schema.json
```

## Licence

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
