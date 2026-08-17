import json
from pathlib import Path

import pytest

from platform_forge.github.release import RELEASE_PLEASE_SHA, initialize_release


def create_python_project(root: Path) -> Path:
    (root / "src/example_package").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[project]",
                'name = "example-package"',
                'version = "0.4.2"',
            ]
        ),
        encoding="utf-8",
    )
    version_file = root / "src/example_package/__init__.py"
    version_file.write_text('__version__ = "0.4.2"\n', encoding="utf-8")
    return version_file


def test_release_initializer_writes_reviewable_python_release_files(tmp_path: Path) -> None:
    version_file = create_python_project(tmp_path)

    written = initialize_release(tmp_path, branch="development")

    workflow = (tmp_path / ".github/workflows/release-please.yml").read_text()
    config = json.loads((tmp_path / "release-please-config.json").read_text())
    manifest = json.loads((tmp_path / ".release-please-manifest.json").read_text())
    assert RELEASE_PLEASE_SHA in workflow
    assert "development" in workflow
    assert "pull-requests: write" in workflow
    assert config["release-type"] == "python"
    assert config["packages"]["."]["package-name"] == "example-package"
    assert config["packages"]["."]["extra-files"] == ["src/example_package/__init__.py"]
    assert manifest == {".": "0.4.2"}
    assert "x-release-please-version" in version_file.read_text()
    assert set(written) == {
        tmp_path / ".github/workflows/release-please.yml",
        tmp_path / "release-please-config.json",
        tmp_path / ".release-please-manifest.json",
        version_file,
    }


def test_release_initializer_refuses_partial_overwrite_before_changing_version_file(
    tmp_path: Path,
) -> None:
    version_file = create_python_project(tmp_path)
    existing = tmp_path / "release-please-config.json"
    existing.write_text("keep me", encoding="utf-8")

    with pytest.raises(FileExistsError):
        initialize_release(tmp_path, branch="development")

    assert existing.read_text(encoding="utf-8") == "keep me"
    assert "x-release-please-version" not in version_file.read_text()


def test_release_initializer_requires_unambiguous_version_file(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "example-package"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="version file"):
        initialize_release(tmp_path, branch="main")
