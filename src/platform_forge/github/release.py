"""Local, reviewable Release Please initialization for Python projects."""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from pathlib import Path
from typing import Any

RELEASE_PLEASE_SHA = "45996ed1f6d02564a971a2fa1b5860e934307cf7"


def _detect_branch(project_root: Path) -> str:
    commands = [
        ["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"],
        ["git", "branch", "--show-current"],
    ]
    for command in commands:
        result = subprocess.run(
            command,
            cwd=project_root,
            capture_output=True,
            check=False,
            text=True,
        )
        value = result.stdout.strip()
        if result.returncode == 0 and value:
            return value.removeprefix("origin/")
    msg = "could not detect a release branch; pass --branch explicitly"
    raise ValueError(msg)


def _project_metadata(project_root: Path) -> tuple[str, str]:
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.is_file():
        raise ValueError("pyproject.toml is required for Python release initialization")
    with pyproject_path.open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)
    project = pyproject.get("project")
    if not isinstance(project, dict):
        raise ValueError("pyproject.toml must contain a [project] table")
    name = project.get("name")
    version = project.get("version")
    if not isinstance(name, str) or not name:
        raise ValueError("pyproject.toml [project].name is required")
    if not isinstance(version, str) or not version:
        raise ValueError("pyproject.toml [project].version is required")
    return name, version


def _resolve_version_file(
    project_root: Path,
    project_name: str,
    version_file: Path | None,
) -> Path:
    if version_file is not None:
        candidate = version_file if version_file.is_absolute() else project_root / version_file
    else:
        package_name = project_name.replace("-", "_").replace(".", "_")
        candidate = project_root / "src" / package_name / "__init__.py"
    if not candidate.is_file():
        raise ValueError("could not find an unambiguous Python version file; pass --version-file")
    return candidate


def _annotated_version_content(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    version_pattern = re.compile(r'^\s*__version__\s*=\s*["\'][^"\']+["\']')
    matching = [index for index, line in enumerate(lines) if version_pattern.match(line)]
    if len(matching) != 1:
        raise ValueError("version file must contain exactly one __version__ assignment")
    index = matching[0]
    if "x-release-please-version" not in lines[index]:
        newline = "\n" if lines[index].endswith("\n") else ""
        lines[index] = f"{lines[index].rstrip()}  # x-release-please-version{newline}"
    return "".join(lines)


def _workflow(branch: str) -> str:
    return f"""name: Release Please

on:
  push:
    branches:
      - {branch}

permissions:
  contents: write
  issues: write
  pull-requests: write

concurrency:
  group: release-please-${{{{ github.ref }}}}
  cancel-in-progress: false

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@{RELEASE_PLEASE_SHA} # v5.0.0
        with:
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json
"""


def initialize_release(
    project_root: Path,
    *,
    branch: str | None = None,
    version_file: Path | None = None,
    force: bool = False,
) -> list[Path]:
    """Write Release Please source files after validating all targets."""
    root = project_root.resolve()
    project_name, version = _project_metadata(root)
    resolved_version_file = _resolve_version_file(root, project_name, version_file)
    release_branch = branch or _detect_branch(root)
    targets = [
        root / ".github/workflows/release-please.yml",
        root / "release-please-config.json",
        root / ".release-please-manifest.json",
    ]
    existing = [path for path in targets if path.exists()]
    if existing and not force:
        raise FileExistsError(existing[0])

    relative_version_file = resolved_version_file.relative_to(root).as_posix()
    config: dict[str, Any] = {
        "$schema": (
            "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json"
        ),
        "release-type": "python",
        "packages": {
            ".": {
                "package-name": project_name,
                "extra-files": [relative_version_file],
            }
        },
    }
    contents = [
        _workflow(release_branch),
        json.dumps(config, indent=2) + "\n",
        json.dumps({".": version}, indent=2) + "\n",
    ]

    for target, content in zip(targets, contents, strict=True):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    resolved_version_file.write_text(
        _annotated_version_content(resolved_version_file),
        encoding="utf-8",
    )
    return [*targets, resolved_version_file]
