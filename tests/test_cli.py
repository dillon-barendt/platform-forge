from pathlib import Path

from typer.testing import CliRunner

from platform_forge.cli import app
from platform_forge.commands.new import build_gateway_config

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def test_doctor_command() -> None:
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Platform Forge Doctor" in result.stdout


def test_new_gateway_generates_project(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "new",
            "gateway",
            "--project-name",
            "Ticket Platform",
            "--domain",
            "ticketing",
            "--providers",
            "ticketmaster,seatgeek",
            "--services",
            "pricing,inventory",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    generated = tmp_path / "ticket-platform"
    assert (generated / "Makefile").exists()
    assert (generated / "apps/gateway/src/ticket_platform_gateway/main.py").exists()


def test_interactive_mode_uses_prompt_values(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["new", "gateway", "--interactive", "--output-dir", str(tmp_path)],
        input="Ticket Platform\nticketing\nticketmaster\npricing\n",
    )

    assert result.exit_code == 0
    assert (tmp_path / "ticket-platform").exists()


def test_non_ai_fallback_uses_defaults() -> None:
    config = build_gateway_config(
        project_name=None,
        domain=None,
        providers=None,
        services=None,
        frontend="vite",
        event_bus="redis",
        observability="logfire",
        interactive=False,
        from_description=None,
    )

    assert config.workspace.project_slug == "gateway-platform"
    assert config.providers[0].name == "example-provider"
