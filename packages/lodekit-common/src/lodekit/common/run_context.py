"""Correlation context for one run of a lodekit component."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any, Self
from uuid import UUID, uuid4

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

COMPONENT_PATTERN = r"^[a-z][a-z0-9_.-]*$"
"""Allowed component names, e.g. ``lodekit-flow`` or ``lodekit.agents.team``."""

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=128)]


def _utcnow() -> datetime:
    return datetime.now(UTC)


class RunContext(BaseModel):
    """Identifies one run of a lodekit component and links it to its parent run.

    A run is one unit of work, such as a pipeline execution, a quality check or an agent
    invocation. Components pass the context down so logs, traces, lineage and quality results
    of nested runs can be correlated. Instances are immutable; use
    [child][lodekit.common.RunContext.child] to derive the context of a nested run.

    Example:
        ```python
        from lodekit.common import RunContext

        pipeline = RunContext(component="lodekit-flow", tags=("nightly",))
        check = pipeline.child("lodekit-quality")
        assert check.parent_run_id == pipeline.run_id
        ```
    """

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        title="RunContext",
        json_schema_serialization_defaults_required=True,
        json_schema_extra={"description": "Correlation context of one run of a lodekit component."},
    )

    run_id: UUID = Field(default_factory=uuid4, description="Unique identifier of this run.")
    parent_run_id: UUID | None = Field(
        default=None, description="Identifier of the run that started this run, if any."
    )
    component: str = Field(
        min_length=1,
        max_length=128,
        pattern=COMPONENT_PATTERN,
        description="Name of the component executing the run, e.g. `lodekit-flow`.",
    )
    started_at: AwareDatetime = Field(
        default_factory=_utcnow, description="Timezone-aware start time of the run."
    )
    tags: tuple[Tag, ...] = Field(
        default=(), description="Free-form labels; duplicates are removed, order is kept."
    )

    @field_validator("tags")
    @classmethod
    def _dedupe_tags(cls, tags: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(dict.fromkeys(tags))

    @model_validator(mode="after")
    def _not_own_parent(self) -> Self:
        if self.parent_run_id == self.run_id:
            msg = "parent_run_id must differ from run_id"
            raise ValueError(msg)
        return self

    def child(self, component: str, *, tags: tuple[str, ...] = ()) -> Self:
        """Return the context of a new run started by this run.

        The child gets a fresh ``run_id`` and start time, ``parent_run_id`` set to this run's id,
        and this run's tags followed by ``tags``.
        """
        return type(self)(parent_run_id=self.run_id, component=component, tags=(*self.tags, *tags))


def run_context_json_schema() -> dict[str, Any]:
    """Return the JSON schema (draft 2020-12) of [RunContext][lodekit.common.RunContext].

    The schema describes serialized payloads (`model_dump(mode="json")`), so every field is
    required. It is part of the public contract and is covered by a snapshot test.
    """
    schema = RunContext.model_json_schema(mode="serialization")
    return {"$schema": JSON_SCHEMA_DIALECT, **schema}


__all__ = [
    "COMPONENT_PATTERN",
    "JSON_SCHEMA_DIALECT",
    "RunContext",
    "Tag",
    "run_context_json_schema",
]
