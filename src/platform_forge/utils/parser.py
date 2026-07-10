"""Configuration parsing helpers for CLI input."""

from __future__ import annotations

from typing import cast

import typer

from platform_forge.core.config import ForgeSettings, FrontendFramework, EventBusProvider, ObservabilityProvider
from platform_forge.core.errors import ConfigurationError
from platform_forge.core.models import (
    GatewayScaffoldConfig,
)
from platform_forge.utils.strings import split_csv


def _validated_choice(value: str, choices: set[str], option_name: str) -> str:
    if value not in choices:
        allowed = ", ".join(sorted(choices))
        raise ConfigurationError(f"{option_name} must be one of: {allowed}")
    return value


def build_gateway_config_from_cli(
    *,
    project_name: str | None,
    domain: str | None,
    providers: str | None,
    services: str | None,
    frontend: str,
    event_bus: str,
    observability: str,
    interactive: bool,
    settings: ForgeSettings | None = None,
) -> GatewayScaffoldConfig:
    """Build a validated gateway core from CLI flags and optional prompts."""
    forge_settings = settings or ForgeSettings()

    if interactive:
        project_name = project_name or typer.prompt(
            "Project name", default=forge_settings.default_project_name
        )
        domain = domain or typer.prompt("Domain", default=forge_settings.default_domain)
        providers = providers or typer.prompt(
            "Providers (comma-separated)",
            default=",".join(forge_settings.default_providers),
        )
        services = services or typer.prompt(
            "Internal services (comma-separated)",
            default=",".join(forge_settings.default_services),
        )

    provider_names = split_csv(providers) or forge_settings.default_providers
    service_names = split_csv(services) or forge_settings.default_services
    frontend_choice = cast(
        FrontendFramework,
        _validated_choice(frontend, forge_settings.frontend_choices, "--frontend"),
    )
    event_bus_choice = cast(
        EventBusProvider,
        _validated_choice(event_bus, forge_settings.event_bus_choices, "--event-bus"),
    )
    observability_choice = cast(
        ObservabilityProvider,
        _validated_choice(observability, forge_settings.observability_choices, "--observability"),
    )

    return GatewayScaffoldConfig.from_cli(
        project_name=project_name or forge_settings.default_project_name,
        domain=domain or forge_settings.default_domain,
        providers=provider_names,
        services=service_names,
        frontend=frontend_choice,
        event_bus=event_bus_choice,
        observability=observability_choice,
    )
