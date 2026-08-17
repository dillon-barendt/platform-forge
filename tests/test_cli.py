from pathlib import Path

from typer.testing import CliRunner

from platform_forge.cli import app
from platform_forge.commands.new import build_gateway_config
from platform_forge.github.gateway import PreflightResult
from platform_forge.github.reconcile import (
    OrganizationSnapshot,
    PlannedOperation,
    RepositoryState,
)

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


def test_ai_mode_falls_back_to_manual_config_without_provider() -> None:
    config = build_gateway_config(
        project_name="Ticket Platform",
        domain="ticketing",
        providers="ticketmaster",
        services="pricing",
        frontend="vite",
        event_bus="redis",
        observability="logfire",
        interactive=False,
        from_description="Build a marketplace for ticket inventory.",
    )

    assert config.workspace.project_slug == "ticket-platform"
    assert config.providers[0].name == "ticketmaster"


def test_github_init_config_creates_strict_starter_file(tmp_path: Path) -> None:
    destination = tmp_path / "governance.toml"

    result = runner.invoke(
        app,
        [
            "github",
            "init-config",
            "--organization",
            "example-org",
            "--repository",
            "api",
            "--repository",
            "web",
            "--output",
            str(destination),
        ],
    )

    assert result.exit_code == 0
    assert destination.is_file()
    assert 'organization = "example-org"' in destination.read_text()


class FakeGateway:
    def __init__(self) -> None:
        self.executed: list[str] = []

    def preflight(self, config: object) -> PreflightResult:
        return PreflightResult(
            account="octocat",
            organization_role="admin",
            repositories=["api"],
        )

    def read_snapshot(self, config: object, repositories: list[str]) -> OrganizationSnapshot:
        return OrganizationSnapshot(
            repositories={name: RepositoryState(name=name) for name in repositories}
        )

    def execute(self, operation: PlannedOperation) -> None:
        self.executed.append(operation.target)


def write_minimal_governance(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "schema_version = 1",
                'organization = "example-org"',
                'repositories = ["api"]',
                "topics = []",
                "teams = []",
                "labels = []",
                "[project]",
                'title = "Roadmap"',
                "fields = []",
                "[ruleset]",
                'name = "Default branch"',
                "[release]",
                "repositories = []",
            ]
        ),
        encoding="utf-8",
    )


def test_github_plan_check_returns_two_when_drift_exists(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "governance.toml"
    write_minimal_governance(config_path)
    gateway = FakeGateway()
    monkeypatch.setattr("platform_forge.commands.github.gateway_factory", lambda: gateway)

    result = runner.invoke(
        app,
        ["github", "plan", "--config", str(config_path), "--check"],
    )

    assert result.exit_code == 2
    assert "CREATE" in result.stdout
    assert gateway.executed == []


def test_github_apply_requires_yes_before_mutation(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "governance.toml"
    write_minimal_governance(config_path)
    gateway = FakeGateway()
    monkeypatch.setattr("platform_forge.commands.github.gateway_factory", lambda: gateway)

    result = runner.invoke(app, ["github", "apply", "--config", str(config_path)])

    assert result.exit_code == 2
    assert "--yes" in result.stdout
    assert gateway.executed == []


def test_github_apply_executes_reviewed_mutations_with_yes(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "governance.toml"
    write_minimal_governance(config_path)
    gateway = FakeGateway()
    monkeypatch.setattr("platform_forge.commands.github.gateway_factory", lambda: gateway)

    result = runner.invoke(
        app,
        ["github", "apply", "--config", str(config_path), "--yes"],
    )

    assert result.exit_code == 0
    assert gateway.executed == ["Roadmap", "Roadmap:api", "Default branch"]


def test_github_init_release_explains_remote_follow_up(tmp_path: Path) -> None:
    (tmp_path / "src/example_package").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "example-package"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (tmp_path / "src/example_package/__init__.py").write_text(
        '__version__ = "0.1.0"\n', encoding="utf-8"
    )

    result = runner.invoke(
        app,
        [
            "github",
            "init-release",
            "--project-root",
            str(tmp_path),
            "--branch",
            "development",
        ],
    )

    assert result.exit_code == 0
    assert "release repositories list" in " ".join(result.stdout.split())
