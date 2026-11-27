"""Contract tests: the public API and the RunContext JSON schema must not change unnoticed.

To accept an intended change, regenerate the snapshot and review the diff:

    LODEKIT_UPDATE_SNAPSHOTS=1 uv run pytest packages/lodekit-common/tests/contract
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import lodekit.common
from lodekit.common import RunContext, run_context_json_schema

pytestmark = pytest.mark.contract

SNAPSHOT = Path(__file__).parent / "snapshots" / "run_context.schema.json"


def test_run_context_schema_matches_snapshot() -> None:
    current = json.dumps(run_context_json_schema(), indent=2, sort_keys=True) + "\n"
    if os.environ.get("LODEKIT_UPDATE_SNAPSHOTS") == "1":
        SNAPSHOT.write_text(current, encoding="utf-8", newline="\n")
    assert SNAPSHOT.read_text(encoding="utf-8") == current, (
        "RunContext JSON schema changed; see this module's docstring to update the snapshot"
    )


def test_schema_declares_dialect_and_requires_every_field() -> None:
    schema = run_context_json_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert sorted(schema["required"]) == sorted(RunContext.model_fields)
    assert schema["additionalProperties"] is False


def test_public_api() -> None:
    assert sorted(lodekit.common.__all__) == [
        "COMPONENT_PATTERN",
        "RunContext",
        "__version__",
        "run_context_json_schema",
    ]
    assert list(RunContext.model_fields) == [
        "run_id",
        "parent_run_id",
        "component",
        "started_at",
        "tags",
    ]


def test_lodekit_is_a_namespace_package() -> None:
    import lodekit  # noqa: PLC0415

    assert getattr(lodekit, "__file__", None) is None
