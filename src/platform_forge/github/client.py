"""Safe subprocess wrapper for the GitHub CLI."""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable
from subprocess import CompletedProcess
from typing import Any

GITHUB_API_VERSION = "2026-03-10"
_TOKEN_PATTERN = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")

Runner = Callable[[list[str], str | None], CompletedProcess[str]]


class GitHubCommandError(RuntimeError):
    """Raised when a GitHub CLI command cannot produce a valid result."""


def _default_runner(args: list[str], input_text: str | None) -> CompletedProcess[str]:
    return subprocess.run(
        args,
        input=input_text,
        capture_output=True,
        check=False,
        text=True,
    )


def _redact(value: str) -> str:
    return _TOKEN_PATTERN.sub("<redacted>", value)


class GhClient:
    """Run `gh` using explicit argument lists and structured JSON boundaries."""

    def __init__(self, runner: Runner | None = None) -> None:
        self._runner = runner or _default_runner

    def command_text(self, args: list[str], *, input_text: str | None = None) -> str:
        """Run a GitHub CLI command and return stdout."""
        command = ["gh", *args]
        result = self._runner(command, input_text)
        if result.returncode != 0:
            detail = _redact(result.stderr.strip() or result.stdout.strip() or "unknown error")
            raise GitHubCommandError(f"GitHub command failed: {detail}")
        return result.stdout

    def command_json(
        self,
        args: list[str],
        *,
        input_data: dict[str, Any] | None = None,
    ) -> Any:
        """Run a command whose stdout is JSON and decode its response."""
        input_text = json.dumps(input_data) if input_data is not None else None
        stdout = self.command_text(args, input_text=input_text)
        if not stdout.strip():
            return None
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            msg = f"GitHub command returned invalid JSON: {_redact(stdout.strip())}"
            raise GitHubCommandError(msg) from exc

    def api(
        self,
        path: str,
        *,
        method: str = "GET",
        data: dict[str, Any] | None = None,
    ) -> Any:
        """Call the versioned GitHub REST API through `gh api`."""
        args = [
            "api",
            path,
            "--method",
            method,
            "--header",
            "Accept: application/vnd.github+json",
            "--header",
            f"X-GitHub-Api-Version: {GITHUB_API_VERSION}",
        ]
        if data is not None:
            args.extend(["--input", "-"])
        return self.command_json(args, input_data=data)

    def api_paginated(self, path: str) -> list[Any]:
        """Read every page from a list REST endpoint."""
        pages = self.command_json(
            [
                "api",
                path,
                "--method",
                "GET",
                "--header",
                "Accept: application/vnd.github+json",
                "--header",
                f"X-GitHub-Api-Version: {GITHUB_API_VERSION}",
                "--paginate",
                "--slurp",
            ]
        )
        if not isinstance(pages, list):
            raise GitHubCommandError("paginated GitHub response was not a list")
        return [item for page in pages for item in page]

    def graphql(self, query: str, variables: dict[str, Any]) -> Any:
        """Call the GitHub GraphQL API with JSON variables."""
        return self.command_json(
            [
                "api",
                "graphql",
                "--header",
                "Accept: application/vnd.github+json",
                "--header",
                f"X-GitHub-Api-Version: {GITHUB_API_VERSION}",
                "--input",
                "-",
            ],
            input_data={"query": query, "variables": variables},
        )
