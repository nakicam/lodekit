"""Enforce the ADR-000 dependency licence policy on the current environment.

Run it inside an environment that contains only runtime dependencies, e.g.::

    uv sync --all-packages --no-dev --locked
    uv run --no-sync python scripts/check_licenses.py

Policy and exceptions live in ``[tool.lodekit.license-check]`` of the root ``pyproject.toml``.
Each installed distribution is classified by, in order: its PEP 639 ``License-Expression``,
its trove classifiers, its free-text ``License`` field. Unknown or disallowed licences fail.
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CLASSIFIERS = {
    "License :: OSI Approved :: MIT License": "MIT",
    "License :: OSI Approved :: MIT No Attribution License (MIT-0)": "MIT-0",
    "License :: OSI Approved :: BSD License": "BSD-3-Clause",
    "License :: OSI Approved :: Apache Software License": "Apache-2.0",
    "License :: OSI Approved :: ISC License (ISCL)": "ISC",
    "License :: OSI Approved :: Python Software Foundation License": "PSF-2.0",
    "License :: OSI Approved :: GNU General Public License (GPL)": "GPL",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)": "GPL-3.0",
    "License :: OSI Approved :: GNU Affero General Public License v3": "AGPL-3.0",
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)": "LGPL-3.0",
    "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
}

FREE_TEXT = {
    "mit": "MIT",
    "mit license": "MIT",
    "the mit license": "MIT",
    "bsd": "BSD-3-Clause",
    "bsd license": "BSD-3-Clause",
    "new bsd": "BSD-3-Clause",
    "new bsd license": "BSD-3-Clause",
    "3-clause bsd license": "BSD-3-Clause",
    "bsd 3-clause": "BSD-3-Clause",
    "bsd-2-clause": "BSD-2-Clause",
    "apache 2.0": "Apache-2.0",
    "apache-2": "Apache-2.0",
    "apache license 2.0": "Apache-2.0",
    "apache license, version 2.0": "Apache-2.0",
    "apache software license": "Apache-2.0",
    "apache software license 2.0": "Apache-2.0",
    "isc": "ISC",
    "isc license": "ISC",
    "psf": "PSF-2.0",
    "psf license": "PSF-2.0",
    "python software foundation license": "PSF-2.0",
}

MAX_INLINE_LICENSE = 80
_TOKEN = re.compile(r"\(|\)|[^\s()]+")


@dataclass(frozen=True)
class Verdict:
    """Licence classification of one installed distribution."""

    name: str
    version: str
    license: str
    allowed: bool
    note: str = ""


def _normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def expression_allowed(expression: str, allowed: frozenset[str]) -> bool:
    """Evaluate an SPDX expression: ``OR`` needs one allowed side, ``AND`` needs both."""
    tokens = _TOKEN.findall(expression)
    pos = 0

    def parse_or() -> bool:
        nonlocal pos
        result = parse_and()
        while pos < len(tokens) and tokens[pos].upper() == "OR":
            pos += 1
            right = parse_and()
            result = result or right
        return result

    def parse_and() -> bool:
        nonlocal pos
        result = parse_atom()
        while pos < len(tokens) and tokens[pos].upper() == "AND":
            pos += 1
            right = parse_atom()
            result = result and right
        return result

    def parse_atom() -> bool:
        nonlocal pos
        if pos >= len(tokens):
            raise ValueError(f"incomplete SPDX expression: {expression!r}")
        item = tokens[pos]
        pos += 1
        if item == "(":
            result = parse_or()
            if pos >= len(tokens) or tokens[pos] != ")":
                raise ValueError(f"unbalanced SPDX expression: {expression!r}")
            pos += 1
            return result
        if pos < len(tokens) and tokens[pos].upper() == "WITH":
            pos += 2  # licence exceptions (e.g. LLVM-exception) do not change the base licence
        return item.removesuffix("+") in allowed

    result = parse_or()
    if pos != len(tokens):
        raise ValueError(f"unexpected token in SPDX expression: {expression!r}")
    return result


def _field(meta: metadata.PackageMetadata, key: str) -> str | None:
    values = meta.get_all(key)
    return str(values[0]) if values else None


def classify(dist: metadata.Distribution, allowed: frozenset[str]) -> tuple[str, bool]:
    """Return the detected licence and whether it is allowed."""
    meta = dist.metadata
    expression = _field(meta, "License-Expression")
    if expression:
        return expression, expression_allowed(expression, allowed)

    found = [CLASSIFIERS[c] for c in meta.get_all("Classifier") or [] if c in CLASSIFIERS]
    if found:
        # Several licence classifiers usually mean "choose one" (dual licensing).
        return " OR ".join(found), any(f in allowed for f in found)

    text = (_field(meta, "License") or "").strip()
    spdx = FREE_TEXT.get(text.lower().rstrip("."))
    if spdx is None and text and "\n" not in text and len(text) < MAX_INLINE_LICENSE:
        try:
            return text, expression_allowed(text, allowed)
        except ValueError:
            pass
    if spdx:
        return spdx, spdx in allowed
    return (text.splitlines()[0][:60] if text else "UNKNOWN"), False


def load_config(root: Path = ROOT) -> tuple[frozenset[str], dict[str, str]]:
    """Read the allow list and per-package exceptions from the root pyproject."""
    with (root / "pyproject.toml").open("rb") as fh:
        config = tomllib.load(fh)["tool"]["lodekit"]["license-check"]
    exceptions = {_normalize(k): str(v) for k, v in config.get("exceptions", {}).items()}
    return frozenset(config["allow"]), exceptions


def check(
    distributions: list[metadata.Distribution],
    allowed: frozenset[str],
    exceptions: dict[str, str],
) -> list[Verdict]:
    """Classify all distributions, applying documented exceptions."""
    verdicts: dict[str, Verdict] = {}
    for dist in distributions:
        name = _normalize(dist.metadata["Name"])
        license_, ok = classify(dist, allowed)
        note = ""
        if not ok and name in exceptions:
            ok, note = True, f"exception: {exceptions[name]}"
        verdicts[name] = Verdict(name, dist.version, license_, ok, note)
    return sorted(verdicts.values(), key=lambda v: v.name)


def main(argv: list[str] | None = None) -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--markdown", type=Path, help="append a Markdown report to this file")
    args = parser.parse_args(argv)

    allowed, exceptions = load_config()
    verdicts = check(list(metadata.distributions()), allowed, exceptions)
    failures = [v for v in verdicts if not v.allowed]

    for v in verdicts:
        status = "ok  " if v.allowed else "FAIL"
        print(f"{status} {v.name}=={v.version}: {v.license} {v.note}".rstrip())
    if args.markdown:
        lines = ["## Dependency licences", "", "| Package | Version | Licence | Status |"]
        lines.append("|---|---|---|---|")
        for v in verdicts:
            status = "ok" if v.allowed else "**FAIL**"
            lines.append(f"| {v.name} | {v.version} | {v.license} | {status} {v.note} |")
        with args.markdown.open("a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    if failures:
        print(
            f"\n{len(failures)} distribution(s) violate the ADR-000 licence policy. Core "
            "dependencies must be MIT, BSD, Apache-2.0, ISC or PSF licensed; move others to an "
            "optional extra or document an exception in [tool.lodekit.license-check].",
            file=sys.stderr,
        )
        return 1
    print(f"\n{len(verdicts)} distribution(s) comply with the ADR-000 licence policy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
