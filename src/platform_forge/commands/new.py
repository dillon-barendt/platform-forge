"""`platform-forge new` command implementation."""

from __future__ import annotations

from pathlib import Path

import typer

from platform_forge.ai import AIUnavailableError, DomainConfigParser
from platform_forge.core.config import ForgeSettings
from platform_forge.core.errors import ConfigurationError
from platform_forge.core.models import GatewayScaffoldConfig
from platform_forge.core.parser import build_gateway_config_from_cli
from platform_forge.templates import ScaffoldGenerator
from platform_forge.utils.console import console


def build_gateway_config(
    *,
    project_name: str | None,
    domain: str | None,
    providers: str | None,
    services: str | None,
    frontend: str,
    event_bus: str,
    observability: str,
    interactive: bool,
    from_description: str | None,
) -> GatewayScaffoldConfig:
    """Build a validated gateway config from CLI flags or prompts."""
    try:
        baseline = build_gateway_config_from_cli(
            project_name=project_name,
            domain=domain,
            providers=providers,
            services=services,
            frontend=frontend,
            event_bus=event_bus,
            observability=observability,
            interactive=interactive,
        )
    except ConfigurationError as exc:
        raise typer.BadParameter(str(exc)) from exc

    if not from_description:
        return baseline

    settings = ForgeSettings()
    try:
        return DomainConfigParser(model=settings.ai_model).parse(
            from_description, baseline=baseline
        )
    except AIUnavailableError:
        console.print(
            "[yellow]AI configuration parsing is unavailable; using manual scaffold config.[/]"
        )
        return baseline


def create_gateway(
    *,
    project_name: str | None,
    domain: str | None,
    providers: str | None,
    services: str | None,
    frontend: str,
    event_bus: str,
    observability: str,
    interactive: bool,
    output_dir: Path,
    from_description: str | None,
    generator: ScaffoldGenerator | None = None,
) -> Path:
    """Create a gateway scaffold and return the generated project path."""
    config = build_gateway_config(
        project_name=project_name,
        domain=domain,
        providers=providers,
        services=services,
        frontend=frontend,
        event_bus=event_bus,
        observability=observability,
        interactive=interactive,
        from_description=from_description,
    )
    generated_path = (generator or ScaffoldGenerator()).generate_gateway(config, output_dir)
    console.print(f"[green]Created gateway scaffold:[/] {generated_path}")
    return generated_path
