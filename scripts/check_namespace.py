"""Guard the PEP 420 ``lodekit.*`` namespace (ADR-001).

Usage (from the repository root)::

    python scripts/check_namespace.py                 # check package configuration
    python scripts/check_namespace.py --wheels dist   # also check built wheels in dist/

Configuration rules for every publishable package below ``packages/``:

* ``[tool.uv.build-backend].module-name`` is set and dotted: ``lodekit.<pkg>``,
* ``module-name = "lodekit"`` and ``namespace = true`` are forbidden,
* there is no ``src/lodekit/__init__.py``.

Wheel rule: no wheel contains a top-level ``lodekit/__init__.py``; every top-level entry is
``lodekit/`` or the wheel's ``.dist-info``/``.data`` directory.

Standard library only, so it also runs before ``uv sync``.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMESPACE = "lodekit"
MODULE_RE = re.compile(rf"^{NAMESPACE}\.[a-z][a-z0-9_]*$")


def check_config(root: Path = ROOT) -> list[str]:
    """Return namespace problems in the package configuration below ``root/packages``."""
    problems: list[str] = []
    for pyproject in sorted(root.glob("packages/*/pyproject.toml")):
        directory = pyproject.parent
        rel = directory.relative_to(root).as_posix()
        with pyproject.open("rb") as fh:
            data = tomllib.load(fh)
        if "build-system" not in data:
            continue
        backend = data.get("tool", {}).get("uv", {}).get("build-backend", {})
        module = backend.get("module-name")
        if backend.get("namespace") is True:
            problems.append(f"{rel}: `namespace = true` is forbidden; use a dotted module-name")
        if module is None:
            problems.append(f'{rel}: set [tool.uv.build-backend] module-name = "{NAMESPACE}.<pkg>"')
        elif module == NAMESPACE:
            problems.append(
                f'{rel}: module-name = "{NAMESPACE}" is forbidden (it owns the namespace)'
            )
        elif not isinstance(module, str) or not MODULE_RE.match(module):
            problems.append(f"{rel}: module-name {module!r} must match {MODULE_RE.pattern}")
        if (directory / "src" / NAMESPACE / "__init__.py").exists():
            problems.append(f"{rel}: src/{NAMESPACE}/__init__.py must not exist (PEP 420)")
    return problems


def check_wheel(wheel: Path) -> list[str]:
    """Return namespace problems in one built wheel."""
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
    problems: list[str] = []
    if f"{NAMESPACE}/__init__.py" in names:
        problems.append(f"{wheel.name}: contains {NAMESPACE}/__init__.py")
    tops = {n.split("/", 1)[0] for n in names}
    stray = sorted(t for t in tops if t != NAMESPACE and not t.endswith((".dist-info", ".data")))
    if stray:
        problems.append(f"{wheel.name}: unexpected top-level entries {stray}")
    return problems


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--wheels",
        nargs="*",
        type=Path,
        default=[],
        metavar="PATH",
        help="wheel files or directories containing *.whl (missing directories are skipped)",
    )
    args = parser.parse_args(argv)

    problems = check_config()
    wheels: list[Path] = []
    for path in args.wheels:
        wheels.extend(
            sorted(path.glob("*.whl")) if path.is_dir() else [path] if path.exists() else []
        )
    for wheel in wheels:
        problems += check_wheel(wheel)

    for problem in problems:
        print(f"::error::{problem}" if "GITHUB_ACTIONS" in os.environ else problem)
    if problems:
        return 1
    print(f"Namespace guard passed ({len(wheels)} wheel(s) checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
