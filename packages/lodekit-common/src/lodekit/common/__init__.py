"""Shared foundations for lodekit packages."""

from importlib.metadata import PackageNotFoundError, version

from lodekit.common.run_context import COMPONENT_PATTERN, RunContext, run_context_json_schema

try:
    __version__ = version("lodekit-common")
except PackageNotFoundError:  # pragma: no cover - only when running from an unbuilt source tree
    __version__ = "0.0.0"

__all__ = ["COMPONENT_PATTERN", "RunContext", "__version__", "run_context_json_schema"]
