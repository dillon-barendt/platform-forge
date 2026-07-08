"""Doctor command implementation."""

from __future__ import annotations

import shutil
import sys
from importlib.util import find_spec

from rich.table import Table

from platform_forge import __version__
from platform_forge.utils.console import console


def run_doctor() -> int:
    """Print local environment diagnostics."""
    table = Table(title="Platform Forge Doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")

    python_ok = sys.version_info >= (3, 13)
    table.add_row("Python", "ok" if python_ok else "error", sys.version.split()[0])
    table.add_row("Platform Forge", "ok", __version__)

    uv_path = shutil.which("uv")
    table.add_row("uv", "ok" if uv_path else "warning", uv_path or "not found on PATH")

    cookiecutter_ok = find_spec("cookiecutter") is not None
    table.add_row("Cookiecutter", "ok" if cookiecutter_ok else "error", "importable")

    console.print(table)
    return 0 if python_ok and cookiecutter_ok else 1
