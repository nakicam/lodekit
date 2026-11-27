from __future__ import annotations

import importlib.util
import sys
from email.message import Message
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        f"lodekit_{name}", ROOT / "scripts" / f"{name}.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


lic = _load("check_licenses")
ALLOWED = frozenset({"MIT", "Apache-2.0", "BSD-3-Clause", "ISC", "PSF-2.0"})


class FakeDist:
    def __init__(self, name: str, **fields: Any) -> None:
        self.version = "1.0"
        msg = Message()
        msg["Name"] = name
        for key, value in fields.items():
            header = key.replace("_", "-")
            for item in value if isinstance(value, list) else [value]:
                msg[header] = item
        self.metadata = msg


@pytest.mark.unit
@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("MIT", True),
        ("GPL-3.0-only", False),
        ("MIT OR GPL-3.0-only", True),
        ("MIT AND GPL-3.0-only", False),
        ("(Apache-2.0 OR MIT) AND BSD-3-Clause", True),
        ("Apache-2.0 WITH LLVM-exception", True),
        ("LGPL-2.1-or-later OR (AGPL-3.0 AND MIT)", False),
    ],
)
def test_expression_allowed(expression: str, expected: bool) -> None:
    assert lic.expression_allowed(expression, ALLOWED) is expected


@pytest.mark.unit
@pytest.mark.parametrize("expression", ["(MIT", "MIT OR", "MIT )"])
def test_expression_allowed_rejects_malformed(expression: str) -> None:
    with pytest.raises(ValueError, match="SPDX"):
        lic.expression_allowed(expression, ALLOWED)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ({"License_Expression": "Apache-2.0"}, ("Apache-2.0", True)),
        (
            {"Classifier": ["License :: OSI Approved :: MIT License", "Typing :: Typed"]},
            ("MIT", True),
        ),
        (
            {"Classifier": "License :: OSI Approved :: GNU Affero General Public License v3"},
            ("AGPL-3.0", False),
        ),
        ({"License": "BSD License"}, ("BSD-3-Clause", True)),
        ({"License": "Proprietary"}, ("Proprietary", False)),
        ({}, ("UNKNOWN", False)),
    ],
)
def test_classify(fields: dict[str, Any], expected: tuple[str, bool]) -> None:
    assert lic.classify(FakeDist("pkg", **fields), ALLOWED) == expected


@pytest.mark.unit
def test_check_applies_documented_exceptions() -> None:
    dists = [
        FakeDist("Soda_Core", License="Proprietary"),
        FakeDist("mystery", License="Proprietary"),
        FakeDist("ok", License_Expression="MIT"),
    ]

    verdicts = lic.check(dists, ALLOWED, {"soda-core": "reviewed"})

    assert [(v.name, v.allowed) for v in verdicts] == [
        ("mystery", False),
        ("ok", True),
        ("soda-core", True),
    ]
    assert verdicts[2].note == "exception: reviewed"


@pytest.mark.unit
def test_repository_policy_matches_adr_000() -> None:
    allowed, _ = lic.load_config(ROOT)

    assert {"MIT", "Apache-2.0", "BSD-3-Clause", "ISC", "PSF-2.0"} <= allowed
    assert not any(lic_id.startswith(("GPL", "AGPL", "LGPL", "MPL")) for lic_id in allowed)
