"""Workspace helper for local development and CI.

Usage (from the repository root)::

    uv run python scripts/dev.py list [--json]
    uv run python scripts/dev.py typecheck [MEMBER ...] [--no-root]
    uv run python scripts/dev.py test [MEMBER ...] [--no-root] [-- PYTEST_ARGS ...]
    uv run python scripts/dev.py check-license-files

MEMBER is a workspace member name such as ``lodekit-common``. Without members, all are used.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMBER_GLOBS = ("packages/*", "examples/*")
LICENSE_FILES = ("LICENSE", "NOTICE")
PYTEST_NO_TESTS_COLLECTED = 5


@dataclass(frozen=True)
class Member:
    """A uv workspace member."""

    name: str
    path: str
    kind: str
    module: str | None
    publishable: bool
    workspace_deps: list[str] = field(default_factory=list)


def _table(data: dict[str, object], key: str) -> dict[str, object]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def _dep_name(requirement: str) -> str:
    for sep in ("[", "<", ">", "=", "!", "~", ";", " ", "@"):
        requirement = requirement.split(sep, 1)[0]
    return requirement.strip().lower().replace("_", "-")


def discover(root: Path = ROOT) -> list[Member]:
    """Return all workspace members below ``packages/`` and ``examples/``, sorted by name."""
    raw: list[tuple[Path, dict[str, object]]] = []
    for pattern in MEMBER_GLOBS:
        for pyproject in sorted(root.glob(f"{pattern}/pyproject.toml")):
            with pyproject.open("rb") as fh:
                raw.append((pyproject.parent, tomllib.load(fh)))

    names = {str(_table(data, "project")["name"]).lower() for _, data in raw}
    members: list[Member] = []
    for directory, data in raw:
        project = _table(data, "project")
        dependencies = project.get("dependencies", [])
        deps = [_dep_name(str(d)) for d in dependencies] if isinstance(dependencies, list) else []
        module = _table(_table(_table(data, "tool"), "uv"), "build-backend").get("module-name")
        relative = directory.relative_to(root).as_posix()
        members.append(
            Member(
                name=str(project["name"]).lower(),
                path=relative,
                kind=relative.split("/", 1)[0],
                module=str(module) if module else None,
                publishable=relative.startswith("packages/") and "build-system" in data,
                workspace_deps=sorted(d for d in deps if d in names),
            )
        )
    return sorted(members, key=lambda m: m.name)


def select(members: list[Member], names: list[str]) -> list[Member]:
    """Filter members by name; raise ``SystemExit`` for unknown names."""
    if not names:
        return members
    by_name = {m.name: m for m in members}
    unknown = sorted(set(names) - by_name.keys())
    if unknown:
        raise SystemExit(f"unknown workspace member(s): {', '.join(unknown)}")
    return [by_name[n] for n in names]


def check_license_files(root: Path = ROOT) -> list[str]:
    """Return problems with the per-package copies of the root licence files."""
    problems: list[str] = []
    for member in discover(root):
        if not member.publishable:
            continue
        for filename in LICENSE_FILES:
            copy = root / member.path / filename
            if not copy.is_file():
                problems.append(f"{member.path}/{filename} is missing")
            elif copy.read_bytes() != (root / filename).read_bytes():
                problems.append(f"{member.path}/{filename} differs from the root {filename}")
    return problems


def _run(cmd: list[str], cwd: Path) -> int:
    where = cwd.relative_to(ROOT).as_posix()
    print(f"+ ({where}) {' '.join(cmd[1:])}", flush=True)
    return subprocess.call(cmd, cwd=cwd)


def typecheck(members: list[Member], *, include_root: bool) -> int:
    """Run mypy --strict per member (namespace-safe) and on the repository tooling."""
    config = str(ROOT / "pyproject.toml")
    status = 0
    for member in members:
        directory = ROOT / member.path
        if member.kind == "examples":
            candidates = [p for p in directory.iterdir() if p.suffix == ".py" or p.is_dir()]
            targets = sorted(p.name for p in candidates if not p.name.startswith((".", "_")))
        else:
            targets = [t for t in ("src", "tests") if (directory / t).is_dir()]
        if targets:
            cmd = [sys.executable, "-m", "mypy", "--config-file", config, *targets]
            status |= _run(cmd, directory)
    if include_root:
        targets = [t for t in ("scripts", "tests") if (ROOT / t).is_dir()]
        status |= _run([sys.executable, "-m", "mypy", "--config-file", config, *targets], ROOT)
    return status


def test(members: list[Member], extra: list[str], *, include_root: bool) -> int:
    """Run pytest per member, with coverage of the member's own module."""
    status = 0
    for member in members:
        tests = ROOT / member.path / "tests"
        if not tests.is_dir():
            continue
        cov = [f"--cov={member.module}", "--cov-report=term-missing"] if member.module else []
        code = _run([sys.executable, "-m", "pytest", tests.as_posix(), *cov, *extra], ROOT)
        status |= 0 if code == PYTEST_NO_TESTS_COLLECTED else code
    if include_root and (ROOT / "tests").is_dir():
        code = _run([sys.executable, "-m", "pytest", "tests", *extra], ROOT)
        status |= 0 if code == PYTEST_NO_TESTS_COLLECTED else code
    return status


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    p_list = sub.add_parser("list", help="list workspace members")
    p_list.add_argument("--json", action="store_true", help="print JSON")
    for name in ("typecheck", "test"):
        p = sub.add_parser(name, help=f"run {name} per member")
        p.add_argument("members", nargs="*")
        p.add_argument("--no-root", action="store_true", help="skip repository-level checks")
    sub.add_parser("check-license-files", help="verify per-package LICENSE/NOTICE copies")

    argv = sys.argv[1:] if argv is None else argv
    extra: list[str] = []
    if "--" in argv:
        split = argv.index("--")
        argv, extra = argv[:split], argv[split + 1 :]
    args = parser.parse_args(argv)
    members = discover()

    if args.command == "list":
        if args.json:
            print(json.dumps([asdict(m) for m in members], indent=2))
        else:
            for m in members:
                print(f"{m.name:30} {m.path}")
        return 0
    if args.command == "typecheck":
        return typecheck(select(members, args.members), include_root=not args.no_root)
    if args.command == "test":
        return test(select(members, args.members), extra, include_root=not args.no_root)
    problems = check_license_files()
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
