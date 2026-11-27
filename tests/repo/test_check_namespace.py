from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "lodekit_check_namespace", ROOT / "scripts" / "check_namespace.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


guard = _load()


def _package(root: Path, name: str, backend: str, *, build: bool = True) -> Path:
    directory = root / "packages" / name
    directory.mkdir(parents=True)
    text = f'[project]\nname = "{name}"\nversion = "0.1.0"\n'
    if build:
        text += '\n[build-system]\nrequires = ["uv_build"]\nbuild-backend = "uv_build"\n'
    text += f"\n[tool.uv.build-backend]\n{backend}\n"
    (directory / "pyproject.toml").write_text(text, encoding="utf-8")
    return directory


def test_dotted_module_name_passes(tmp_path: Path) -> None:
    _package(tmp_path, "lodekit-common", 'module-name = "lodekit.common"')
    _package(tmp_path, "unbuilt", 'module-name = "lodekit"', build=False)
    assert guard.check_config(tmp_path) == []


@pytest.mark.parametrize(
    ("backend", "needle"),
    [
        ('module-name = "lodekit"', "forbidden"),
        ('module-name = "lodekit.common"\nnamespace = true', "namespace = true"),
        ("", "set [tool.uv.build-backend]"),
        ('module-name = "common"', "must match"),
        ('module-name = "lodekit.common.sub"', "must match"),
    ],
)
def test_invalid_configuration_is_reported(tmp_path: Path, backend: str, needle: str) -> None:
    _package(tmp_path, "lodekit-common", backend)
    problems = guard.check_config(tmp_path)
    assert len(problems) == 1
    assert needle in problems[0]


def test_namespace_init_file_is_reported(tmp_path: Path) -> None:
    directory = _package(tmp_path, "lodekit-common", 'module-name = "lodekit.common"')
    init = directory / "src" / "lodekit" / "__init__.py"
    init.parent.mkdir(parents=True)
    init.touch()
    assert guard.check_config(tmp_path) == [
        "packages/lodekit-common: src/lodekit/__init__.py must not exist (PEP 420)"
    ]


def _wheel(path: Path, names: list[str]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name in names:
            zf.writestr(name, "")
    return path


def test_clean_wheel_passes(tmp_path: Path) -> None:
    wheel = _wheel(
        tmp_path / "ok.whl",
        [
            "lodekit/common/__init__.py",
            "lodekit/common/py.typed",
            "lodekit_common-0.1.0.dist-info/METADATA",
        ],
    )
    assert guard.check_wheel(wheel) == []


def test_wheel_with_namespace_init_or_stray_top_level_fails(tmp_path: Path) -> None:
    wheel = _wheel(tmp_path / "bad.whl", ["lodekit/__init__.py", "common/__init__.py"])
    problems = guard.check_wheel(wheel)
    assert any("lodekit/__init__.py" in p for p in problems)
    assert any("['common']" in p for p in problems)


def test_main_checks_wheels_in_directories(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _wheel(tmp_path / "bad.whl", ["lodekit/__init__.py"])
    assert guard.main(["--wheels", str(tmp_path), str(tmp_path / "missing")]) == 1
    assert "bad.whl" in capsys.readouterr().out
