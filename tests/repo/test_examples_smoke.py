from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "lodekit_examples_smoke", ROOT / "scripts" / "examples_smoke.py"
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


smoke = _load()


def _example(tmp_path: Path, table: str) -> Path:
    tmp_path.joinpath("pyproject.toml").write_text(
        '[project]\nname = "example-x"\nversion = "0"\n'
        'dependencies = ["lodekit-common>=0.1", "rich>=13"]\n\n' + table,
        encoding="utf-8",
    )
    return tmp_path


def test_load_config_reads_table_and_defaults(tmp_path: Path) -> None:
    config = smoke.load_config(
        _example(tmp_path, '[tool.lodekit.example]\nrun = ["python", "main.py"]\n')
    )
    assert config.run == ["python", "main.py"]
    assert config.expect == []
    assert config.timeout == smoke.DEFAULT_TIMEOUT
    assert config.dependencies == ["lodekit-common>=0.1", "rich>=13"]


@pytest.mark.parametrize(
    "table",
    [
        "",
        "[tool.lodekit.example]\nrun = []\n",
        '[tool.lodekit.example]\nrun = ["python"]\nexpect = "x"\n',
        '[tool.lodekit.example]\nrun = ["python"]\ntimeout = 0\n',
    ],
)
def test_load_config_rejects_invalid_tables(tmp_path: Path, table: str) -> None:
    with pytest.raises(ValueError, match=r"\[tool\.lodekit\.example\]"):
        smoke.load_config(_example(tmp_path, table))


def _member(name: str, deps: list[str], *, publishable: bool = True) -> object:
    kind = "packages" if publishable else "examples"
    return smoke.Member(
        name=name,
        path=f"{kind}/{name}",
        kind=kind,
        module=None,
        publishable=publishable,
        workspace_deps=deps,
    )


def test_workspace_closure_is_transitive_and_skips_unpublishable() -> None:
    common = _member("lodekit-common", [])
    flow = _member("lodekit-flow", ["lodekit-common"])
    helper = _member("example-helper", [], publishable=False)
    example = _member("example-x", ["lodekit-flow", "example-helper"], publishable=False)
    members = [common, flow, helper, example]
    assert smoke.workspace_closure(example, members) == ["lodekit-common", "lodekit-flow"]


def test_third_party_excludes_workspace_dependencies(tmp_path: Path) -> None:
    config = smoke.load_config(_example(tmp_path, '[tool.lodekit.example]\nrun = ["python"]\n'))
    member = _member("example-x", ["lodekit-common"], publishable=False)
    assert smoke.third_party(config, member) == ["rich>=13"]


def test_sanitized_env_strips_credentials_and_blocks_network() -> None:
    env = smoke.sanitized_env(
        {"PATH": "p", "OPENAI_API_KEY": "k", "GH_TOKEN": "t", "NO_PROXY": "*", "HOME": "h"}
    )
    assert env["PATH"] == "p"
    assert env["HOME"] == "h"
    assert "OPENAI_API_KEY" not in env
    assert "GH_TOKEN" not in env
    assert "NO_PROXY" not in env
    assert env["HTTPS_PROXY"] == smoke.UNREACHABLE_PROXY


def test_check_output_reports_missing_lines() -> None:
    assert smoke.check_output("run_id=1\nok\n", ["run_id=", "done"]) == ["done"]


def test_main_without_examples_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert smoke.main(["--members-json", "[]"]) == 0
    assert "No examples" in capsys.readouterr().out
