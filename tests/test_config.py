import pytest
from pydantic import ValidationError

from platform_forge.config.models import EventBusConfig, GatewayScaffoldConfig, WorkspaceConfig


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
