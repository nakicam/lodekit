from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_dev() -> ModuleType:
    spec = importlib.util.spec_from_file_location("lodekit_dev_script", ROOT / "scripts" / "dev.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


dev = _load_dev()

PACKAGE = """\
[project]
name = "{name}"
version = "0.1.0"
dependencies = [{deps}]

[build-system]
requires = ["uv_build>=0.12,<0.13"]
build-backend = "uv_build"

[tool.uv.build-backend]
module-name = "{module}"
"""


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    _write(tmp_path, "LICENSE", "license text")
    _write(tmp_path, "NOTICE", "notice text")
    _write(
        tmp_path,
        "packages/lodekit-common/pyproject.toml",
        PACKAGE.format(name="lodekit-common", deps='"pydantic>=2,<3"', module="lodekit.common"),
    )
    _write(
        tmp_path,
        "packages/lodekit-flow/pyproject.toml",
        PACKAGE.format(
            name="lodekit-flow",
            deps='"lodekit_common[extra]>=0.1,<0.2", "dlt>=1"',
            module="lodekit.flow",
        ),
    )
    _write(
        tmp_path,
        "examples/hello/pyproject.toml",
        '[project]\nname = "example-hello"\nversion = "0"\ndependencies = ["lodekit-flow"]\n',
    )
    _write(tmp_path, "packages/README.md", "not a member")
    for pkg in ("lodekit-common", "lodekit-flow"):
        _write(tmp_path, f"packages/{pkg}/LICENSE", "license text")
        _write(tmp_path, f"packages/{pkg}/NOTICE", "notice text")
    return tmp_path


@pytest.mark.unit
def test_discover_finds_members_with_workspace_dependencies(workspace: Path) -> None:
    members = {m.name: m for m in dev.discover(workspace)}

    assert sorted(members) == ["example-hello", "lodekit-common", "lodekit-flow"]
    flow = members["lodekit-flow"]
    assert flow.path == "packages/lodekit-flow"
    assert flow.module == "lodekit.flow"
    assert flow.publishable
    assert flow.workspace_deps == ["lodekit-common"]
    hello = members["example-hello"]
    assert hello.kind == "examples"
    assert not hello.publishable
    assert hello.module is None
    assert hello.workspace_deps == ["lodekit-flow"]


@pytest.mark.unit
def test_select_rejects_unknown_members(workspace: Path) -> None:
    members = dev.discover(workspace)

    assert [m.name for m in dev.select(members, ["lodekit-flow"])] == ["lodekit-flow"]
    assert dev.select(members, []) == members
    with pytest.raises(SystemExit, match="lodekit-nope"):
        dev.select(members, ["lodekit-nope"])


@pytest.mark.unit
def test_check_license_files_reports_missing_and_stale_copies(workspace: Path) -> None:
    assert dev.check_license_files(workspace) == []

    (workspace / "packages/lodekit-flow/NOTICE").unlink()
    (workspace / "packages/lodekit-common/LICENSE").write_text("old", encoding="utf-8")

    assert dev.check_license_files(workspace) == [
        "packages/lodekit-common/LICENSE differs from the root LICENSE",
        "packages/lodekit-flow/NOTICE is missing",
    ]


@pytest.mark.unit
def test_repository_license_copies_are_in_sync() -> None:
    assert dev.check_license_files(ROOT) == []


@pytest.mark.unit
def test_namespace_root_has_no_init_file() -> None:
    offenders = sorted(p.as_posix() for p in ROOT.glob("packages/*/src/lodekit/__init__.py"))
    assert offenders == [], "lodekit/ must stay a PEP 420 namespace without __init__.py"
