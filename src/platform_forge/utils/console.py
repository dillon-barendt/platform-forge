"""Rich console helpers used by CLI commands."""

from rich.console import Console

console = Console()
error_console = Console(stderr=True)
