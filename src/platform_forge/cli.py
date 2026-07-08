"""Typer CLI for Platform Forge."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from platform_forge import __version__
from platform_forge.commands.doctor import run_doctor
from platform_forge.commands.new import create_gateway

app = typer.Typer(
    name="platform-forge",
    help="Deterministic scaffolding for modern Python platform architectures.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
new_app = typer.Typer(help="Create a new scaffold.", no_args_is_help=True)
app.add_typer(new_app, name="new")


@app.command()
def version() -> None:
    """Print the Platform Forge version."""
    typer.echo(__version__)


@app.command()
def doctor() -> None:
    """Check the local Platform Forge environment."""
    raise typer.Exit(run_doctor())


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
