from typing import Any

import pytest

from platform_forge.github.client import GitHubCommandError
from platform_forge.github.config import GitHubGovernanceConfig
from platform_forge.github.gateway import GitHubGateway, PreflightError
from platform_forge.github.reconcile import PlannedOperation


class RecordingClient:
    def __init__(self) -> None:
        self.api_calls: list[tuple[str, str, dict[str, Any] | None]] = []
        self.command_calls: list[list[str]] = []
        self.graphql_calls: list[tuple[str, dict[str, Any]]] = []
        self.scope_headers = "x-oauth-scopes: repo, read:org\n"
        self.rulesets_error: str | None = None
        self.project_details: dict[str, Any] | None = None

    def command_text(self, args: list[str], *, input_text: str | None = None) -> str:
        self.command_calls.append(args)
        if args[:3] == ["api", "-i", "user"]:
            return self.scope_headers
        return "authenticated"

    def command_json(
        self,
        args: list[str],
        *,
        input_data: dict[str, Any] | None = None,
    ) -> Any:
        self.command_calls.append(args)
        if args[:2] == ["project", "list"]:
            return {"projects": [{"number": 1, "title": "Roadmap"}]}
        return {"number": 1}

    def api(
        self,
        path: str,
        *,
        method: str = "GET",
        data: dict[str, Any] | None = None,
    ) -> Any:
        self.api_calls.append((path, method, data))
        if path == "orgs/example-org/rulesets" and self.rulesets_error is not None:
            raise GitHubCommandError(self.rulesets_error)
        responses: dict[str, Any] = {
            "user": {"login": "octocat"},
            "orgs/example-org/memberships/octocat": {"role": "admin", "state": "active"},
            "orgs/example-org/rulesets": [],
            "orgs/example-org/actions/permissions": {"enabled_repositories": "selected"},
            "repos/example-org/api": {"id": 42, "name": "api", "archived": False},
        }
        return responses.get(path)

    def graphql(self, query: str, variables: dict[str, Any]) -> Any:
        self.graphql_calls.append((query, variables))
        if self.project_details is not None and "projectV2(number" in query:
            return {"data": {"organization": {"projectV2": self.project_details}}}
        return {"data": {"organization": {"projectsV2": {"nodes": []}}}}


def minimal_config() -> GitHubGovernanceConfig:
    return GitHubGovernanceConfig(
        organization="example-org",
        repositories=["api"],
        teams=[],
        labels=[],
        topics=[],
        project={"fields": []},
    )


def test_preflight_rejects_missing_admin_and_project_scopes() -> None:
    client = RecordingClient()
    gateway = GitHubGateway(client=client, executable_resolver=lambda _: "/usr/bin/gh")

    with pytest.raises(PreflightError, match="admin:org, project"):
        gateway.preflight(minimal_config())

    assert all(method == "GET" for _, method, _ in client.api_calls)


def test_preflight_accepts_required_scopes_and_active_org_admin() -> None:
    client = RecordingClient()
    client.scope_headers = "x-oauth-scopes: repo, admin:org, project\n"
    gateway = GitHubGateway(client=client, executable_resolver=lambda _: "/usr/bin/gh")

    result = gateway.preflight(minimal_config())

    assert result.account == "octocat"
    assert result.organization_role == "admin"
    assert result.repositories == ["api"]
    assert result.rulesets_supported is True


def test_preflight_reports_paid_rulesets_as_unsupported_without_blocking() -> None:
    client = RecordingClient()
    client.scope_headers = "x-oauth-scopes: repo, admin:org, project\n"
    client.rulesets_error = "Upgrade to GitHub Team to enable this feature."
    gateway = GitHubGateway(client=client, executable_resolver=lambda _: "/usr/bin/gh")

    result = gateway.preflight(minimal_config())

    assert result.repositories == ["api"]
    assert result.rulesets_supported is False


def test_team_creation_operation_maps_to_versioned_api_request() -> None:
    client = RecordingClient()
    gateway = GitHubGateway(client=client, executable_resolver=lambda _: "/usr/bin/gh")
    gateway.organization = "example-org"
    operation = PlannedOperation(
        action="create",
        resource="team",
        target="maintainers",
        detail="team settings",
        payload={
            "slug": "maintainers",
            "description": "Repository maintainers",
            "privacy": "closed",
            "permission": "maintain",
        },
    )

    gateway.execute(operation)

    assert client.api_calls[-1] == (
        "orgs/example-org/teams",
        "POST",
        {
            "name": "maintainers",
            "description": "Repository maintainers",
            "privacy": "closed",
        },
    )


def test_workflow_permission_operation_keeps_default_token_read_only() -> None:
    client = RecordingClient()
    gateway = GitHubGateway(client=client, executable_resolver=lambda _: "/usr/bin/gh")
    gateway.organization = "example-org"
    operation = PlannedOperation(
        action="update",
        resource="workflow permissions",
        target="api",
        detail="security-sensitive",
        payload={
            "repository": "api",
            "default_workflow_permissions": "read",
            "can_approve_pull_request_reviews": True,
        },
    )

    gateway.execute(operation)

    assert client.api_calls[-1] == (
        "repos/example-org/api/actions/permissions/workflow",
        "PUT",
        {
            "default_workflow_permissions": "read",
            "can_approve_pull_request_reviews": True,
        },
    )


def test_project_field_create_reuses_reserved_status_field() -> None:
    client = RecordingClient()
    client.project_details = {
        "fields": {
            "nodes": [
                {
                    "id": "PVTF_status",
                    "name": "Status",
                    "options": [
                        {
                            "id": "option_backlog",
                            "name": "Backlog",
                            "color": "GRAY",
                            "description": "",
                        }
                    ],
                }
            ]
        }
    }
    gateway = GitHubGateway(client=client, executable_resolver=lambda _: "/usr/bin/gh")
    gateway.organization = "example-org"
    operation = PlannedOperation(
        action="create",
        resource="project field",
        target="Roadmap:Status",
        detail="single-select project field",
        payload={"project": "Roadmap", "name": "Status", "options": ["Backlog", "Ready"]},
    )

    gateway.execute(operation)

    assert not any(call[:2] == ["project", "field-create"] for call in client.command_calls)
    _, variables = client.graphql_calls[-1]
    assert variables["fieldId"] == "PVTF_status"
    assert variables["options"] == [
        {
            "id": "option_backlog",
            "name": "Backlog",
            "color": "GRAY",
            "description": "",
        },
        {"name": "Ready", "color": "GRAY", "description": ""},
    ]


def test_actions_access_adds_release_repository_to_selected_org_allowlist() -> None:
    client = RecordingClient()
    client.api_calls.clear()
    gateway = GitHubGateway(client=client, executable_resolver=lambda _: "/usr/bin/gh")
    gateway.organization = "example-org"
    operation = PlannedOperation(
        action="update",
        resource="actions access",
        target="api",
        detail="security-sensitive",
        payload={"repository": "api"},
    )

    gateway.execute(operation)

    assert client.api_calls[-1] == (
        "orgs/example-org/actions/permissions/repositories/42",
        "PUT",
        None,
    )


def test_org_workflow_permission_keeps_default_token_read_only() -> None:
    client = RecordingClient()
    client.api_calls.clear()
    gateway = GitHubGateway(client=client, executable_resolver=lambda _: "/usr/bin/gh")
    gateway.organization = "example-org"
    operation = PlannedOperation(
        action="update",
        resource="organization workflow permissions",
        target="example-org",
        detail="security-sensitive",
        payload={
            "default_workflow_permissions": "read",
            "can_approve_pull_request_reviews": True,
        },
    )

    gateway.execute(operation)

    assert client.api_calls[-1] == (
        "orgs/example-org/actions/permissions/workflow",
        "PUT",
        {
            "default_workflow_permissions": "read",
            "can_approve_pull_request_reviews": True,
        },
    )
