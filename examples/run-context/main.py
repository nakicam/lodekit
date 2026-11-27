"""Correlate nested runs with lodekit.common.RunContext (offline, no data)."""

from __future__ import annotations

import json

from lodekit.common import RunContext, run_context_json_schema


def main() -> None:
    pipeline = RunContext(component="lodekit-flow", tags=("nightly",))
    quality = pipeline.child("lodekit-quality", tags=("eu",))

    print(f"pipeline run_id={pipeline.run_id}")
    print(f"quality  run_id={quality.run_id}")
    print(f"quality parent_run_id matches: {quality.parent_run_id == pipeline.run_id}")
    print(f"tags={quality.tags}")
    print(quality.model_dump_json(indent=2))

    schema = run_context_json_schema()
    print(f"schema fields: {', '.join(json.dumps(k) for k in schema['properties'])}")


if __name__ == "__main__":
    main()
