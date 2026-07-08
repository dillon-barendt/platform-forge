"""Cookiecutter-backed scaffold generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cookiecutter.main import cookiecutter  # type: ignore[import-untyped]

from platform_forge.config.models import GatewayScaffoldConfig
from platform_forge.templates.registry import TemplateRegistry


class ScaffoldGenerator:
    """Generate projects from validated scaffold configuration."""

    def __init__(self, registry: TemplateRegistry | None = None) -> None:
        self._registry = registry or TemplateRegistry()

    def generate_gateway(self, config: GatewayScaffoldConfig, output_dir: Path) -> Path:
        template = self._registry.get_template("gateway")
        context: dict[str, Any] = config.to_cookiecutter_context()
        result = cookiecutter(
            str(template.path),
            no_input=True,
            output_dir=str(output_dir),
            extra_context=context,
        )
        return Path(result)
