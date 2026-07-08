"""Configuration parsing helpers for CLI input."""

from __future__ import annotations

from typing import cast

import typer

from platform_forge.config.defaults import (
    DEFAULT_DOMAIN,
    DEFAULT_PROJECT_NAME,
    DEFAULT_PROVIDERS,
    DEFAULT_SERVICES,
    EVENT_BUS_CHOICES,
    FRONTEND_CHOICES,
    OBSERVABILITY_CHOICES,
)
from platform_forge.config.models import (
    EventBusProvider,
    FrontendFramework,
    GatewayScaffoldConfig,
    ObservabilityProvider,
)
from platform_forge.utils.errors import ConfigurationError
from platform_forge.utils.paths import split_csv


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
) -> GatewayScaffoldConfig:
    """Build a validated gateway config from CLI flags and optional prompts."""
    if interactive:
        project_name = project_name or typer.prompt("Project name", default=DEFAULT_PROJECT_NAME)
        domain = domain or typer.prompt("Domain", default=DEFAULT_DOMAIN)
        providers = providers or typer.prompt(
            "Providers (comma-separated)",
            default=",".join(DEFAULT_PROVIDERS),
        )
        services = services or typer.prompt(
            "Internal services (comma-separated)",
            default=",".join(DEFAULT_SERVICES),
        )

    provider_names = split_csv(providers) or DEFAULT_PROVIDERS
    service_names = split_csv(services) or DEFAULT_SERVICES
    frontend_choice = cast(
        FrontendFramework,
        _validated_choice(frontend, FRONTEND_CHOICES, "--frontend"),
    )
    event_bus_choice = cast(
        EventBusProvider,
        _validated_choice(event_bus, EVENT_BUS_CHOICES, "--event-bus"),
    )
    observability_choice = cast(
        ObservabilityProvider,
        _validated_choice(observability, OBSERVABILITY_CHOICES, "--observability"),
    )

    return GatewayScaffoldConfig.from_cli(
        project_name=project_name or DEFAULT_PROJECT_NAME,
        domain=domain or DEFAULT_DOMAIN,
        providers=provider_names,
        services=service_names,
        frontend=frontend_choice,
        event_bus=event_bus_choice,
        observability=observability_choice,
    )
