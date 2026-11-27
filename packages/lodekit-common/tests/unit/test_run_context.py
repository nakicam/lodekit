from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from importlib.metadata import version
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

import lodekit.common
from lodekit.common import RunContext, run_context_json_schema

pytestmark = pytest.mark.unit


def test_defaults_generate_id_and_utc_start() -> None:
    before = datetime.now(UTC)
    ctx = RunContext(component="lodekit-flow")
    assert isinstance(ctx.run_id, UUID)
    assert ctx.parent_run_id is None
    assert before <= ctx.started_at <= datetime.now(UTC)
    assert ctx.started_at.utcoffset() == timedelta(0)
    assert ctx.tags == ()


def test_each_context_gets_a_new_run_id() -> None:
    assert RunContext(component="a").run_id != RunContext(component="a").run_id


def test_is_immutable_and_rejects_unknown_fields() -> None:
    ctx = RunContext(component="a")
    with pytest.raises(ValidationError):
        ctx.component = "b"  # type: ignore[misc]
    with pytest.raises(ValidationError, match="extra"):
        RunContext(component="a", user="x")  # type: ignore[call-arg]


@pytest.mark.parametrize("component", ["", "Flow", "1flow", "lodekit flow", "x" * 129])
def test_rejects_invalid_component(component: str) -> None:
    with pytest.raises(ValidationError):
        RunContext(component=component)


@pytest.mark.parametrize("component", ["a", "lodekit-flow", "lodekit.agents.team", "my_tool2"])
def test_accepts_valid_component(component: str) -> None:
    assert RunContext(component=component).component == component


def test_requires_timezone_aware_start() -> None:
    with pytest.raises(ValidationError, match="timezone"):
        RunContext(component="a", started_at=datetime(2026, 1, 1))
    aware = datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=1)))
    assert RunContext(component="a", started_at=aware).started_at == aware


def test_tags_are_stripped_and_deduplicated_in_order() -> None:
    ctx = RunContext(component="a", tags=(" nightly", "eu", "nightly ", "eu"))
    assert ctx.tags == ("nightly", "eu")


@pytest.mark.parametrize("tag", ["", "   ", "x" * 129])
def test_rejects_invalid_tags(tag: str) -> None:
    with pytest.raises(ValidationError):
        RunContext(component="a", tags=(tag,))


def test_rejects_run_that_is_its_own_parent() -> None:
    run_id = uuid4()
    with pytest.raises(ValidationError, match="parent_run_id must differ"):
        RunContext(component="a", run_id=run_id, parent_run_id=run_id)


def test_child_links_to_parent_and_inherits_tags() -> None:
    parent = RunContext(component="lodekit-flow", tags=("nightly",))
    child = parent.child("lodekit-quality", tags=("eu", "nightly"))
    assert child.parent_run_id == parent.run_id
    assert child.run_id != parent.run_id
    assert child.component == "lodekit-quality"
    assert child.tags == ("nightly", "eu")
    assert child.started_at >= parent.started_at


def test_json_round_trip() -> None:
    ctx = RunContext(component="a", parent_run_id=uuid4(), tags=("x",))
    assert RunContext.model_validate_json(ctx.model_dump_json()) == ctx


def test_module_entry_point_prints_schema(capsys: pytest.CaptureFixture[str]) -> None:
    from lodekit.common.__main__ import main  # noqa: PLC0415

    main()
    assert json.loads(capsys.readouterr().out) == run_context_json_schema()


def test_version_is_exposed() -> None:
    assert lodekit.common.__version__ == version("lodekit-common")
