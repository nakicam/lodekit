"""Run each example against freshly built wheels in a clean virtual environment.

Usage (from the repository root)::

    uv run python scripts/examples_smoke.py [EXAMPLE ...] [--members-json JSON] [--python 3.12]

For every selected example (a workspace member below ``examples/``) this script

1. builds wheels for the workspace packages the example depends on (transitively),
2. creates a fresh venv and installs only those wheels plus the example's declared
   third-party dependencies (no editable installs, no workspace sources),
3. runs ``[tool.lodekit.example].run`` in a copy of the example folder outside the repository,
   with provider API keys removed and HTTP(S) proxies pointing to an unreachable address, and
4. checks the exit code and that every ``expect`` string appears in stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.dev import ROOT, Member, _dep_name, discover, select

UNREACHABLE_PROXY = "http://127.0.0.1:9"
DEFAULT_TIMEOUT = 300
COPY_IGNORE = shutil.ignore_patterns(".venv", "__pycache__", ".pytest_cache", ".mypy_cache")


@dataclass(frozen=True)
class ExampleConfig:
    """The ``[tool.lodekit.example]`` table plus the declared dependencies."""

    run: list[str]
    expect: list[str]
    timeout: int
    dependencies: list[str]


def load_config(directory: Path) -> ExampleConfig:
    """Read and validate the example configuration from ``directory/pyproject.toml``."""
    with (directory / "pyproject.toml").open("rb") as fh:
        data = tomllib.load(fh)
    table = data.get("tool", {}).get("lodekit", {}).get("example")
    if not isinstance(table, dict):
        msg = f"{directory.name}: missing [tool.lodekit.example] table"
        raise ValueError(msg)
    run = table.get("run")
    if not (isinstance(run, list) and run and all(isinstance(a, str) for a in run)):
        msg = f"{directory.name}: [tool.lodekit.example].run must be a non-empty list of strings"
        raise ValueError(msg)
    expect = table.get("expect", [])
    if not (isinstance(expect, list) and all(isinstance(e, str) for e in expect)):
        msg = f"{directory.name}: [tool.lodekit.example].expect must be a list of strings"
        raise ValueError(msg)
    timeout = table.get("timeout", DEFAULT_TIMEOUT)
    if not isinstance(timeout, int) or timeout <= 0:
        msg = f"{directory.name}: [tool.lodekit.example].timeout must be a positive integer"
        raise ValueError(msg)
    deps = data.get("project", {}).get("dependencies", [])
    return ExampleConfig(run=run, expect=expect, timeout=timeout, dependencies=list(deps))


def workspace_closure(member: Member, members: list[Member]) -> list[str]:
    """Return the publishable workspace packages ``member`` depends on, transitively."""
    by_name = {m.name: m for m in members}
    seen: set[str] = set()
    stack = list(member.workspace_deps)
    while stack:
        name = stack.pop()
        if name in seen:
            continue
        seen.add(name)
        stack.extend(by_name[name].workspace_deps)
    return sorted(n for n in seen if by_name[n].publishable)


def third_party(config: ExampleConfig, member: Member) -> list[str]:
    """Return the declared requirements that are not workspace members."""
    workspace = set(member.workspace_deps)
    return [d for d in config.dependencies if _dep_name(d) not in workspace]


def sanitized_env(base: dict[str, str]) -> dict[str, str]:
    """Return an environment without provider credentials and with unreachable proxies."""
    env = {k: v for k, v in base.items() if not k.upper().endswith(("_API_KEY", "_TOKEN"))}
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        env[key] = UNREACHABLE_PROXY
    env.pop("NO_PROXY", None)
    env.pop("no_proxy", None)
    env["PYTHONUTF8"] = "1"
    return env


def check_output(stdout: str, expect: list[str]) -> list[str]:
    """Return the expected substrings missing from ``stdout``."""
    return [e for e in expect if e not in stdout]


def _venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _uv(*args: str) -> None:
    print("+ uv", " ".join(args), flush=True)
    subprocess.run(["uv", *args], cwd=ROOT, check=True)


def build_wheels(packages: list[str], wheelhouse: Path) -> dict[str, Path]:
    """Build one wheel per package into ``wheelhouse`` and return them by package name."""
    wheels: dict[str, Path] = {}
    for package in packages:
        target = wheelhouse / package
        _uv("build", "--package", package, "--wheel", "--no-sources", "--out-dir", str(target))
        (wheel,) = target.glob("*.whl")
        wheels[package] = wheel
    return wheels


def smoke(member: Member, members: list[Member], python: str, work: Path) -> list[str]:
    """Run one example end to end and return a list of problems (empty on success)."""
    directory = ROOT / member.path
    config = load_config(directory)
    wheels = build_wheels(workspace_closure(member, members), work / "wheels")

    venv = work / "venv"
    _uv("venv", "--quiet", "--python", python, str(venv))
    requirements = [str(w) for w in wheels.values()] + third_party(config, member)
    if requirements:
        _uv("pip", "install", "--python", str(_venv_python(venv)), *requirements)

    sandbox = work / "example"
    shutil.copytree(directory, sandbox, ignore=COPY_IGNORE)
    cmd = list(config.run)
    if cmd[0] in {"python", "python3"}:
        cmd[0] = str(_venv_python(venv))
    print(f"+ ({member.name}) {' '.join(config.run)}", flush=True)
    try:
        result = subprocess.run(
            cmd,
            cwd=sandbox,
            env=sanitized_env(dict(os.environ)),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=config.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return [f"{member.name}: timed out after {config.timeout}s"]
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    problems = [f"{member.name}: exit code {result.returncode}"] if result.returncode else []
    problems += [
        f"{member.name}: missing output {e!r}" for e in check_output(result.stdout, config.expect)
    ]
    return problems


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("examples", nargs="*", help="example member names (default: all)")
    parser.add_argument("--members-json", help="JSON list of affected members; others are skipped")
    parser.add_argument("--python", default=f"{sys.version_info.major}.{sys.version_info.minor}")
    args = parser.parse_args(argv)

    members = discover()
    examples = [m for m in select(members, args.examples) if m.kind == "examples"]
    if args.members_json is not None:
        affected = set(json.loads(args.members_json))
        examples = [m for m in examples if m.name in affected]
    if not examples:
        print("No examples to smoke-test.")
        return 0

    failed = 0
    for member in examples:
        with tempfile.TemporaryDirectory(prefix=f"smoke-{member.name}-") as tmp:
            problems = smoke(member, members, args.python, Path(tmp))
        for problem in problems:
            print(f"FAIL {problem}", file=sys.stderr)
        failed += bool(problems)
    print(f"{len(examples) - failed}/{len(examples)} examples passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
