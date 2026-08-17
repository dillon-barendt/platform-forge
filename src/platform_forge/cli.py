"""Typer CLI for Platform Forge."""

from pathlib import Path
from typing import Annotated

import typer

from platform_forge import __version__
from platform_forge.commands.doctor import run_doctor
from platform_forge.commands.github import (
    apply_command,
    init_config_command,
    init_release_command,
    plan_command,
)
from platform_forge.commands.new import create_gateway

app = typer.Typer(
    name="platform-forge",
    help="Deterministic scaffolding for modern Python platform architectures.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
new_app = typer.Typer(help="Create a new scaffold.", no_args_is_help=True)
github_app = typer.Typer(
    help="Plan and apply GitHub organization governance.",
    no_args_is_help=True,
)
app.add_typer(new_app, name="new")
app.add_typer(github_app, name="github")


@app.command()
def version() -> None:
    """Print the Platform Forge version."""
    typer.echo(__version__)


@app.command()
def doctor() -> None:
    """Check the local Platform Forge environment."""
    raise typer.Exit(run_doctor())


@github_app.command("init-config")
def github_init_config(
    organization: Annotated[
        str,
        typer.Option("--organization", help="GitHub organization login."),
    ],
    repository: Annotated[
        list[str],
        typer.Option(
            "--repository",
            help="Repository to manage; repeat this option, or pass '*' alone.",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option("--output", help="Destination TOML configuration."),
    ] = Path("platform-forge.github.toml"),
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite an existing destination."),
    ] = False,
) -> None:
    """Create a strict starter governance configuration."""
    raise typer.Exit(
        init_config_command(
            organization=organization,
            repositories=repository,
            output=output,
            force=force,
        )
    )


@github_app.command("plan")
def github_plan(
    config: Annotated[
        Path,
        typer.Option("--config", help="Governance TOML configuration."),
    ] = Path("platform-forge.github.toml"),
    check: Annotated[
        bool,
        typer.Option("--check", help="Return exit code 2 when drift exists."),
    ] = False,
) -> None:
    """Preview governance changes without mutating GitHub."""
    raise typer.Exit(plan_command(config_path=config, check=check))


@github_app.command("apply")
def github_apply(
    config: Annotated[
        Path,
        typer.Option("--config", help="Governance TOML configuration."),
    ] = Path("platform-forge.github.toml"),
    yes: Annotated[
        bool,
        typer.Option("--yes", help="Confirm the reviewed remote mutations."),
    ] = False,
) -> None:
    """Apply an upsert-only governance plan."""
    raise typer.Exit(apply_command(config_path=config, yes=yes))


@github_app.command("init-release")
def github_init_release(
    project_root: Annotated[
        Path | None,
        typer.Option("--project-root", help="Python repository root."),
    ] = None,
    branch: Annotated[
        str | None,
        typer.Option("--branch", help="Release target branch; detected by default."),
    ] = None,
    version_file: Annotated[
        Path | None,
        typer.Option(
            "--version-file",
            help="Python file containing the __version__ assignment.",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite existing Release Please files."),
    ] = False,
) -> None:
    """Add reviewable Release Please files to the local checkout."""
    raise typer.Exit(
        init_release_command(
            project_root=project_root or Path.cwd(),
            branch=branch,
            version_file=version_file,
            force=force,
        )
    )


@new_app.command()
def gateway(
    project_name: Annotated[
        str | None,
        typer.Option("--project-name", help="Human-readable project name."),
    ] = None,
    domain: Annotated[
        str | None,
        typer.Option("--domain", help="Product or business domain."),
    ] = None,
    providers: Annotated[
        str | None,
        typer.Option("--providers", help="Comma-separated external providers."),
    ] = None,
    services: Annotated[
        str | None,
        typer.Option("--services", help="Comma-separated internal services."),
    ] = None,
    frontend: Annotated[
        str,
        typer.Option("--frontend", help="Frontend scaffold: none, vite, nextjs."),
    ] = "vite",
    event_bus: Annotated[
        str,
        typer.Option("--event-bus", help="Event bus: none, redis, nats, kafka."),
    ] = "redis",
    observability: Annotated[
        str,
        typer.Option(
            "--observability", help="Observability provider: none, logfire, opentelemetry."
        ),
    ] = "logfire",
    interactive: Annotated[
        bool,
        typer.Option("--interactive", help="Prompt for missing scaffold options."),
    ] = False,
    output_dir: Annotated[
        Path | None,
        typer.Option("--output-dir", help="Directory where the scaffold is created."),
    ] = None,
    from_description: Annotated[
        str | None,
        typer.Option(
            "--from-description",
            help="Use optional Pydantic AI parsing to derive config from a domain description.",
        ),
    ] = None,
) -> None:
    """Create a modern Python gateway scaffold."""
    create_gateway(
        project_name=project_name,
        domain=domain,
        providers=providers,
        services=services,
        frontend=frontend,
        event_bus=event_bus,
        observability=observability,
        interactive=interactive,
        output_dir=output_dir or Path.cwd(),
        from_description=from_description,
    )
