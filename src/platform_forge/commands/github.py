"""Implementation for `platform-forge github` commands."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError
from rich.table import Table

from platform_forge.github.config import GitHubGovernanceConfig, write_starter_config
from platform_forge.github.gateway import GitHubGateway, PreflightError
from platform_forge.github.reconcile import (
    ApplyResult,
    GovernanceApplier,
    GovernancePlanner,
    PlannedOperation,
)
from platform_forge.github.release import initialize_release
from platform_forge.utils.console import console, error_console

gateway_factory: Any = GitHubGateway


def _operations_table(
    title: str,
    operations: list[PlannedOperation] | list[ApplyResult],
) -> Table:
    table = Table(title=title)
    table.add_column("Action")
    table.add_column("Resource")
    table.add_column("Target")
    table.add_column("Detail")
    for operation in operations:
        table.add_row(
            operation.action.upper(),
            operation.resource,
            operation.target,
            operation.detail,
        )
    return table


def init_config_command(
    *,
    organization: str,
    repositories: list[str],
    output: Path,
    force: bool,
) -> int:
    """Create a beginner-ready governance configuration."""
    try:
        destination = write_starter_config(
            output,
            organization=organization,
            repositories=repositories,
            force=force,
        )
    except (FileExistsError, ValidationError, ValueError) as exc:
        error_console.print(f"[red]Could not create configuration:[/] {exc}")
        return 1
    console.print(f"[green]Created GitHub governance configuration:[/] {destination}")
    return 0


def _build_plan(config_path: Path) -> tuple[Any, list[PlannedOperation]]:
    config = GitHubGovernanceConfig.from_toml(config_path)
    gateway = gateway_factory()
    preflight = gateway.preflight(config)
    snapshot = gateway.read_snapshot(config, preflight.repositories)
    return gateway, GovernancePlanner(config, snapshot).build()


def plan_command(*, config_path: Path, check: bool) -> int:
    """Read GitHub state and display a mutation-free governance plan."""
    try:
        _, operations = _build_plan(config_path)
    except (OSError, ValidationError, ValueError, PreflightError) as exc:
        error_console.print(f"[red]GitHub governance preflight failed:[/] {exc}")
        return 1
    console.print(_operations_table("GitHub governance plan", operations))
    drift = any(operation.action in {"create", "update"} for operation in operations)
    return 2 if check and drift else 0


def apply_command(*, config_path: Path, yes: bool) -> int:
    """Apply a reviewed upsert-only governance plan."""
    if not yes:
        console.print("[red]Refusing to mutate GitHub without --yes.[/]")
        return 2
    try:
        gateway, operations = _build_plan(config_path)
    except (OSError, ValidationError, ValueError, PreflightError) as exc:
        error_console.print(f"[red]GitHub governance preflight failed:[/] {exc}")
        return 1
    console.print(_operations_table("Reviewed GitHub governance plan", operations))
    results = GovernanceApplier(gateway).apply(operations)
    console.print(_operations_table("GitHub governance apply results", results))
    return 1 if any(result.action == "failed" for result in results) else 0


def init_release_command(
    *,
    project_root: Path,
    branch: str | None,
    version_file: Path | None,
    force: bool,
) -> int:
    """Create local Release Please files for review and commit."""
    try:
        written = initialize_release(
            project_root,
            branch=branch,
            version_file=version_file,
            force=force,
        )
    except (OSError, ValueError, FileExistsError) as exc:
        error_console.print(f"[red]Could not initialize releases:[/] {exc}")
        return 1
    console.print("[green]Created reviewable Release Please files:[/]")
    for path in written:
        console.print(f"- {path}")
    console.print(
        "[yellow]Before the workflow can open release PRs, mark this repository in "
        "the release repositories list and apply the governance configuration.[/]"
    )
    return 0
