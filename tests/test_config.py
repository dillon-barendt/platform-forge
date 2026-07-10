import pytest
from pydantic import ValidationError

from platform_forge.core.config import ForgeSettings
from platform_forge.core.models import EventBusConfig, GatewayScaffoldConfig, WorkspaceConfig
from platform_forge.core.parser import build_gateway_config_from_cli


def test_workspace_derives_slug_and_package_name() -> None:
    workspace = WorkspaceConfig(project_name="Ticket Platform", domain="ticketing")

    assert workspace.project_slug == "ticket-platform"
    assert workspace.package_name == "ticket_platform"


def test_gateway_context_is_deterministic() -> None:
    config = GatewayScaffoldConfig.from_cli(
        project_name="Ticket Platform",
        domain="ticketing",
        providers=["Ticketmaster", "SeatGeek"],
        services=["Pricing", "Inventory"],
        frontend="vite",
        event_bus="redis",
        observability="logfire",
    )

    context = config.to_cookiecutter_context()

    assert context["project_slug"] == "ticket-platform"
    assert context["scaffold_config"]["workspace"]["project_slug"] == "ticket-platform"
    assert context["gateway_package"] == "ticket_platform_gateway"
    assert context["providers"] == [
        {"name": "ticketmaster", "display_name": "Ticketmaster"},
        {"name": "seatgeek", "display_name": "Seatgeek"},
    ]
    assert context["services"][0] == {"name": "pricing", "port": 8100}


def test_duplicate_providers_are_rejected() -> None:
    with pytest.raises(ValidationError, match="provider names must be unique"):
        GatewayScaffoldConfig.from_cli(
            project_name="Ticket Platform",
            domain="ticketing",
            providers=["Ticketmaster", "ticketmaster"],
            services=["Pricing"],
            frontend="vite",
            event_bus="redis",
            observability="logfire",
        )


def test_enum_validation_rejects_unknown_event_bus() -> None:
    with pytest.raises(ValidationError):
        EventBusConfig(provider="rabbitmq")


def test_forge_settings_own_cli_defaults() -> None:
    settings = ForgeSettings(
        default_project_name="Tickets",
        default_domain="ticketing",
        default_providers=["ticketmaster"],
        default_services=["pricing"],
    )

    config = build_gateway_config_from_cli(
        project_name=None,
        domain=None,
        providers=None,
        services=None,
        frontend="vite",
        event_bus="redis",
        observability="logfire",
        interactive=False,
        settings=settings,
    )

    assert config.workspace.project_name == "Tickets"
    assert config.workspace.domain == "ticketing"
    assert config.providers[0].name == "ticketmaster"
    assert config.services[0].name == "pricing"


def test_forge_settings_load_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLATFORM_FORGE_DEFAULT_PROVIDERS", '["stripe", "adyen"]')
    monkeypatch.setenv("PLATFORM_FORGE_EVENT_BUS_CHOICES", '["none", "redis"]')

    settings = ForgeSettings()

    assert settings.default_providers == ["stripe", "adyen"]
    assert settings.event_bus_choices == {"none", "redis"}
