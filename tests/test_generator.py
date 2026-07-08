from pathlib import Path

from platform_forge.config.models import GatewayScaffoldConfig
from platform_forge.templates import ScaffoldGenerator


def test_generator_creates_expected_gateway_files(tmp_path: Path) -> None:
    config = GatewayScaffoldConfig.from_cli(
        project_name="Ticket Platform",
        domain="ticketing",
        providers=["ticketmaster"],
        services=["pricing"],
        frontend="vite",
        event_bus="redis",
        observability="logfire",
    )

    generated = ScaffoldGenerator().generate_gateway(config, tmp_path)

    assert generated == tmp_path / "ticket-platform"
    assert (generated / ".env.example").exists()
    assert (generated / "apps/gateway/.env.example").exists()
    assert (generated / "apps/web/.env.example").exists()
    assert "make dev" in (generated / "README.md").read_text()
