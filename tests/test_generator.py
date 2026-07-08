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
    assert (generated / "package.json").exists()
    assert (generated / "pnpm-workspace.yaml").exists()
    assert "make dev" in (generated / "README.md").read_text()


def test_generated_makefile_is_canonical_interface(tmp_path: Path) -> None:
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
    makefile = (generated / "Makefile").read_text()

    for target in (
        "install:",
        "dev:",
        "dev-gateway:",
        "dev-web:",
        "redis:",
        "test:",
        "lint:",
        "format:",
        "typecheck:",
        "doctor:",
    ):
        assert target in makefile

    assert "-include .env" in makefile
    assert "uv sync --all-packages" in makefile
    assert "docker compose up -d redis" in makefile
    assert "uv run --all-packages fastapi dev" in makefile
    assert "pnpm install --config.dangerouslyAllowAllBuilds=true" in makefile
    assert "pnpm --filter web run dev" in makefile


def test_generated_environment_ownership_is_layered(tmp_path: Path) -> None:
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
    root_env = (generated / ".env.example").read_text()
    gateway_env = (generated / "apps/gateway/.env.example").read_text()
    settings = (generated / "apps/gateway/src/ticket_platform_gateway/settings.py").read_text()

    assert "COMPOSE_PROJECT_NAME=ticket-platform" in root_env
    assert "REDIS_URL=redis://localhost:6379/0" in root_env
    assert "GATEWAY_APP_NAME=Ticket Platform" in gateway_env
    assert 'env_prefix="GATEWAY_"' in settings
    assert 'env_file=(".env", "apps/gateway/.env")' in settings
