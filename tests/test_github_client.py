import json
from subprocess import CompletedProcess

import pytest

from platform_forge.github.client import GhClient, GitHubCommandError


def test_api_uses_argument_list_pinned_version_and_json_stdin() -> None:
    calls: list[tuple[list[str], str | None]] = []

    def runner(args: list[str], input_text: str | None) -> CompletedProcess[str]:
        calls.append((args, input_text))
        return CompletedProcess(args, 0, stdout='{"ok": true}', stderr="")

    client = GhClient(runner=runner)
    result = client.api("orgs/example/teams", method="POST", data={"name": "maintainers"})

    assert result == {"ok": True}
    assert calls == [
        (
            [
                "gh",
                "api",
                "orgs/example/teams",
                "--method",
                "POST",
                "--header",
                "Accept: application/vnd.github+json",
                "--header",
                "X-GitHub-Api-Version: 2026-03-10",
                "--input",
                "-",
            ],
            json.dumps({"name": "maintainers"}),
        )
    ]


def test_failed_command_redacts_github_tokens() -> None:
    def runner(args: list[str], input_text: str | None) -> CompletedProcess[str]:
        return CompletedProcess(
            args,
            1,
            stdout="",
            stderr="request failed with ghp_abcdefghijklmnopqrstuvwxyz0123456789",
        )

    client = GhClient(runner=runner)

    with pytest.raises(GitHubCommandError) as exc_info:
        client.command_json(["repo", "view"])

    message = str(exc_info.value)
    assert "ghp_abcdefghijklmnopqrstuvwxyz0123456789" not in message
    assert "<redacted>" in message


def test_malformed_json_is_reported_as_a_command_error() -> None:
    def runner(args: list[str], input_text: str | None) -> CompletedProcess[str]:
        return CompletedProcess(args, 0, stdout="not-json", stderr="")

    client = GhClient(runner=runner)

    with pytest.raises(GitHubCommandError, match="invalid JSON"):
        client.command_json(["project", "list", "--format", "json"])
