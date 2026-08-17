"""Live GitHub gateway for governance snapshots and reviewed mutations."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from typing import Any, Protocol, cast
from urllib.parse import quote

from platform_forge.github.client import GhClient, GitHubCommandError
from platform_forge.github.config import GitHubGovernanceConfig
from platform_forge.github.reconcile import (
    LabelState,
    OrganizationSnapshot,
    PlannedOperation,
    ProjectState,
    RepositoryState,
    RulesetState,
    TeamState,
)


class GitHubClientProtocol(Protocol):
    def command_text(self, args: list[str], *, input_text: str | None = None) -> str: ...

    def command_json(
        self,
        args: list[str],
        *,
        input_data: dict[str, Any] | None = None,
    ) -> Any: ...

    def api(
        self,
        path: str,
        *,
        method: str = "GET",
        data: dict[str, Any] | None = None,
    ) -> Any: ...

    def api_paginated(self, path: str) -> list[Any]: ...

    def graphql(self, query: str, variables: dict[str, Any]) -> Any: ...


class PreflightError(RuntimeError):
    """Raised before mutation when GitHub access is insufficient or ambiguous."""


@dataclass(frozen=True)
class PreflightResult:
    """Verified GitHub identity and target scope."""

    account: str
    organization_role: str
    repositories: list[str]
    rulesets_supported: bool = True


class GitHubGateway:
    """Observe and mutate only the resources declared by one organization config."""

    def __init__(
        self,
        client: GitHubClientProtocol | None = None,
        *,
        executable_resolver: Any = shutil.which,
    ) -> None:
        self._client = client or GhClient()
        self._executable_resolver = executable_resolver
        self.organization: str | None = None
        self.rulesets_supported = True

    def preflight(self, config: GitHubGovernanceConfig) -> PreflightResult:
        """Verify tooling, identity, scopes, organization role, and repositories."""
        if self._executable_resolver("gh") is None:
            raise PreflightError("GitHub CLI is not installed or is not on PATH")
        try:
            self._client.command_text(["auth", "status", "--active"])
            user = cast(dict[str, Any], self._client.api("user"))
            account = str(user["login"])
            membership = cast(
                dict[str, Any],
                self._client.api(f"orgs/{config.organization}/memberships/{account}"),
            )
        except (GitHubCommandError, KeyError, TypeError) as exc:
            raise PreflightError(f"GitHub authentication preflight failed: {exc}") from exc

        role = str(membership.get("role", ""))
        state = str(membership.get("state", ""))
        if role != "admin" or state != "active":
            raise PreflightError(
                f"{account} is not an active organization administrator for {config.organization}"
            )

        scope_headers = self._client.command_text(["api", "-i", "user"])
        scopes = self._parse_oauth_scopes(scope_headers)
        if scopes:
            required = {"admin:org", "project"}
            missing = sorted(required - scopes)
            if missing:
                raise PreflightError(
                    "GitHub token is missing required scopes: " + ", ".join(missing)
                )

        try:
            self._client.api(f"orgs/{config.organization}/rulesets")
            self.rulesets_supported = True
        except GitHubCommandError as exc:
            if "upgrade to github team" not in str(exc).lower():
                raise PreflightError(
                    f"GitHub organization ruleset administration is unavailable: {exc}"
                ) from exc
            self.rulesets_supported = False

        try:
            self._client.command_json(
                [
                    "project",
                    "list",
                    "--owner",
                    config.organization,
                    "--limit",
                    "1",
                    "--format",
                    "json",
                ]
            )
            repositories = self._resolve_repositories(config)
        except GitHubCommandError as exc:
            raise PreflightError(
                "GitHub organization administration, project, or repository access is missing: "
                f"{exc}"
            ) from exc

        self.organization = config.organization
        return PreflightResult(
            account=account,
            organization_role=role,
            repositories=repositories,
            rulesets_supported=self.rulesets_supported,
        )

    @staticmethod
    def _parse_oauth_scopes(headers: str) -> set[str]:
        match = re.search(r"^x-oauth-scopes:\s*(.*)$", headers, flags=re.IGNORECASE | re.MULTILINE)
        if match is None or not match.group(1).strip():
            return set()
        return {scope.strip() for scope in match.group(1).split(",") if scope.strip()}

    def _resolve_repositories(self, config: GitHubGovernanceConfig) -> list[str]:
        if config.repositories == ["*"]:
            repositories = self._paginate(f"orgs/{config.organization}/repos?type=all&per_page=100")
            return sorted(
                str(repository["name"])
                for repository in repositories
                if not bool(repository.get("archived"))
            )
        resolved: list[str] = []
        for name in config.repositories:
            repository = cast(
                dict[str, Any], self._client.api(f"repos/{config.organization}/{name}")
            )
            if bool(repository.get("archived")):
                raise PreflightError(f"selected repository is archived: {name}")
            resolved.append(name)
        return resolved

    def _paginate(self, path: str) -> list[Any]:
        method = getattr(self._client, "api_paginated", None)
        if method is not None:
            return cast(list[Any], method(path))
        response = self._client.api(path)
        return cast(list[Any], response or [])

    def read_snapshot(
        self,
        config: GitHubGovernanceConfig,
        repositories: list[str],
    ) -> OrganizationSnapshot:
        """Read all managed resource categories without changing GitHub."""
        self.organization = config.organization
        repository_states = {
            repository: self._read_repository(repository) for repository in repositories
        }
        team_states = self._read_teams(config)
        project_state = self._read_project(config.project.title)
        ruleset_state = self._read_ruleset(config.ruleset.name) if self.rulesets_supported else None
        organization_workflow = cast(
            dict[str, Any],
            self._client.api(f"orgs/{config.organization}/actions/permissions/workflow"),
        )
        return OrganizationSnapshot(
            repositories=repository_states,
            teams=team_states,
            project=project_state,
            ruleset=ruleset_state,
            rulesets_supported=self.rulesets_supported,
            organization_workflow_permissions=(
                str(organization_workflow.get("default_workflow_permissions", "read")),
                bool(organization_workflow.get("can_approve_pull_request_reviews", False)),
            ),
        )

    def _read_repository(self, repository: str) -> RepositoryState:
        organization = self._organization()
        labels_data = self._paginate(f"repos/{organization}/{repository}/labels?per_page=100")
        labels = {
            str(label["name"]): LabelState(
                color=str(label["color"]).upper(),
                description=str(label.get("description") or ""),
            )
            for label in labels_data
        }
        topics_data = cast(
            dict[str, Any], self._client.api(f"repos/{organization}/{repository}/topics")
        )
        permissions = cast(
            dict[str, Any],
            self._client.api(f"repos/{organization}/{repository}/actions/permissions/workflow"),
        )
        actions_permissions = cast(
            dict[str, Any],
            self._client.api(f"repos/{organization}/{repository}/actions/permissions"),
        )
        return RepositoryState(
            name=repository,
            labels=labels,
            topics={str(name) for name in topics_data.get("names", [])},
            actions_enabled=bool(actions_permissions.get("enabled", False)),
            workflow_permissions=(
                str(permissions.get("default_workflow_permissions", "read")),
                bool(permissions.get("can_approve_pull_request_reviews", False)),
            ),
        )

    def _read_teams(self, config: GitHubGovernanceConfig) -> dict[str, TeamState]:
        organization = self._organization()
        team_data = self._paginate(f"orgs/{organization}/teams?per_page=100")
        by_slug = {str(team["slug"]): team for team in team_data}
        states: dict[str, TeamState] = {}
        for desired in config.teams:
            team = by_slug.get(desired.slug)
            if team is None:
                continue
            members = self._paginate(
                f"orgs/{organization}/teams/{desired.slug}/members?per_page=100"
            )
            repositories = self._paginate(
                f"orgs/{organization}/teams/{desired.slug}/repos?per_page=100"
            )
            states[desired.slug] = TeamState(
                description=str(team.get("description") or ""),
                privacy=str(team.get("privacy") or "closed"),
                members={str(member["login"]) for member in members},
                repository_permissions={
                    str(repository["name"]): self._repository_permission(repository)
                    for repository in repositories
                },
            )
        return states

    @staticmethod
    def _repository_permission(repository: dict[str, Any]) -> str:
        permissions = cast(dict[str, Any], repository.get("permissions") or {})
        for name in ("admin", "maintain", "push", "triage", "pull"):
            if permissions.get(name):
                return name
        return "pull"

    def _read_project(self, title: str) -> ProjectState | None:
        response = cast(
            dict[str, Any],
            self._client.graphql(_PROJECT_QUERY, {"organization": self._organization()}),
        )
        nodes = (
            response.get("data", {}).get("organization", {}).get("projectsV2", {}).get("nodes", [])
        )
        project = next((node for node in nodes if node.get("title") == title), None)
        if project is None:
            return None
        fields: dict[str, set[str]] = {}
        for node in project.get("fields", {}).get("nodes", []):
            if node.get("options") is not None:
                fields[str(node["name"])] = {
                    str(option["name"]) for option in node.get("options", [])
                }
        return ProjectState(
            title=str(project["title"]),
            description=str(project.get("shortDescription") or ""),
            visibility="PUBLIC" if bool(project.get("public")) else "PRIVATE",
            fields=fields,
            linked_repositories={
                str(repository["name"])
                for repository in project.get("repositories", {}).get("nodes", [])
            },
        )

    def _read_ruleset(self, name: str) -> RulesetState | None:
        organization = self._organization()
        rulesets = cast(list[dict[str, Any]], self._client.api(f"orgs/{organization}/rulesets"))
        summary = next((ruleset for ruleset in rulesets if ruleset.get("name") == name), None)
        if summary is None:
            return None
        details = cast(
            dict[str, Any],
            self._client.api(f"orgs/{organization}/rulesets/{summary['id']}"),
        )
        return RulesetState(payload=self._canonical_ruleset(details))

    @staticmethod
    def _canonical_ruleset(ruleset: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": ruleset["name"],
            "target": ruleset.get("target", "branch"),
            "enforcement": ruleset["enforcement"],
            "conditions": ruleset["conditions"],
            "rules": ruleset.get("rules", []),
            "bypass_actors": ruleset.get("bypass_actors", []),
        }

    def execute(self, operation: PlannedOperation) -> None:
        """Execute one reviewed create or update operation."""
        handlers = {
            "team": self._execute_team,
            "team member": self._execute_team_member,
            "repository permission": self._execute_repository_permission,
            "label": self._execute_label,
            "topics": self._execute_topics,
            "project": self._execute_project,
            "project field": self._execute_project_field,
            "project link": self._execute_project_link,
            "ruleset": self._execute_ruleset,
            "organization workflow permissions": self._execute_organization_workflow_permissions,
            "actions access": self._execute_actions_access,
            "workflow permissions": self._execute_workflow_permissions,
        }
        handler = handlers.get(operation.resource)
        if handler is None:
            raise ValueError(f"unsupported governance resource: {operation.resource}")
        handler(operation)

    def _execute_team(self, operation: PlannedOperation) -> None:
        organization = self._organization()
        payload = {
            "name": operation.payload["slug"],
            "description": operation.payload["description"],
            "privacy": operation.payload["privacy"],
        }
        if operation.action == "create":
            self._client.api(f"orgs/{organization}/teams", method="POST", data=payload)
        else:
            self._client.api(
                f"orgs/{organization}/teams/{operation.payload['slug']}",
                method="PATCH",
                data=payload,
            )

    def _execute_team_member(self, operation: PlannedOperation) -> None:
        organization = self._organization()
        self._client.api(
            f"orgs/{organization}/teams/{operation.payload['team']}/memberships/"
            f"{operation.payload['member']}",
            method="PUT",
            data={"role": operation.payload["role"]},
        )

    def _execute_repository_permission(self, operation: PlannedOperation) -> None:
        organization = self._organization()
        self._client.api(
            f"orgs/{organization}/teams/{operation.payload['team']}/repos/{organization}/"
            f"{operation.payload['repository']}",
            method="PUT",
            data={"permission": operation.payload["permission"]},
        )

    def _execute_label(self, operation: PlannedOperation) -> None:
        organization = self._organization()
        repository = operation.payload["repository"]
        payload = {
            "name": operation.payload["name"],
            "color": operation.payload["color"],
            "description": operation.payload["description"],
        }
        if operation.action == "create":
            path = f"repos/{organization}/{repository}/labels"
            method = "POST"
        else:
            name = quote(str(operation.payload["name"]), safe="")
            path = f"repos/{organization}/{repository}/labels/{name}"
            method = "PATCH"
        self._client.api(path, method=method, data=payload)

    def _execute_topics(self, operation: PlannedOperation) -> None:
        organization = self._organization()
        self._client.api(
            f"repos/{organization}/{operation.payload['repository']}/topics",
            method="PUT",
            data={"names": operation.payload["topics"]},
        )

    def _execute_project(self, operation: PlannedOperation) -> None:
        organization = self._organization()
        if operation.action == "create":
            created = cast(
                dict[str, Any],
                self._client.command_json(
                    [
                        "project",
                        "create",
                        "--owner",
                        organization,
                        "--title",
                        str(operation.payload["title"]),
                        "--format",
                        "json",
                    ]
                ),
            )
            number = int(created["number"])
        else:
            number = self._project_number(str(operation.payload["title"]))
        self._client.command_json(
            [
                "project",
                "edit",
                str(number),
                "--owner",
                organization,
                "--description",
                str(operation.payload["description"]),
                "--visibility",
                str(operation.payload["visibility"]),
                "--format",
                "json",
            ]
        )

    def _execute_project_field(self, operation: PlannedOperation) -> None:
        organization = self._organization()
        number = self._project_number(str(operation.payload["project"]))
        options = [str(option) for option in operation.payload["options"]]
        project = self._project_details(number)
        field = next(
            (
                node
                for node in project["fields"]["nodes"]
                if node.get("name") == operation.payload["name"]
            ),
            None,
        )
        if operation.action == "create" and field is None:
            self._client.command_json(
                [
                    "project",
                    "field-create",
                    str(number),
                    "--owner",
                    organization,
                    "--name",
                    str(operation.payload["name"]),
                    "--data-type",
                    "SINGLE_SELECT",
                    "--single-select-options",
                    ",".join(options),
                    "--format",
                    "json",
                ]
            )
            return
        if field is None:
            raise RuntimeError(f"project field was not found: {operation.payload['name']}")
        existing = {option["name"]: option for option in field.get("options", [])}
        option_inputs = [
            {
                **({"id": existing[name]["id"]} if name in existing else {}),
                "name": name,
                "color": existing.get(name, {}).get("color", "GRAY"),
                "description": existing.get(name, {}).get("description", ""),
            }
            for name in options
        ]
        self._client.graphql(
            _UPDATE_FIELD_MUTATION,
            {"fieldId": field["id"], "name": field["name"], "options": option_inputs},
        )

    def _execute_project_link(self, operation: PlannedOperation) -> None:
        organization = self._organization()
        number = self._project_number(str(operation.payload["project"]))
        self._client.command_text(
            [
                "project",
                "link",
                str(number),
                "--owner",
                organization,
                "--repo",
                f"{organization}/{operation.payload['repository']}",
            ]
        )

    def _execute_ruleset(self, operation: PlannedOperation) -> None:
        organization = self._organization()
        if operation.action == "create":
            path = f"orgs/{organization}/rulesets"
            method = "POST"
        else:
            rulesets = cast(list[dict[str, Any]], self._client.api(f"orgs/{organization}/rulesets"))
            ruleset = next(
                item for item in rulesets if item.get("name") == operation.payload["name"]
            )
            path = f"orgs/{organization}/rulesets/{ruleset['id']}"
            method = "PUT"
        self._client.api(path, method=method, data=operation.payload)

    def _execute_workflow_permissions(self, operation: PlannedOperation) -> None:
        organization = self._organization()
        repository = operation.payload["repository"]
        self._client.api(
            f"repos/{organization}/{repository}/actions/permissions/workflow",
            method="PUT",
            data={
                "default_workflow_permissions": operation.payload["default_workflow_permissions"],
                "can_approve_pull_request_reviews": operation.payload[
                    "can_approve_pull_request_reviews"
                ],
            },
        )

    def _execute_organization_workflow_permissions(self, operation: PlannedOperation) -> None:
        self._client.api(
            f"orgs/{self._organization()}/actions/permissions/workflow",
            method="PUT",
            data={
                "default_workflow_permissions": operation.payload["default_workflow_permissions"],
                "can_approve_pull_request_reviews": operation.payload[
                    "can_approve_pull_request_reviews"
                ],
            },
        )

    def _execute_actions_access(self, operation: PlannedOperation) -> None:
        organization = self._organization()
        repository = str(operation.payload["repository"])
        policy = cast(dict[str, Any], self._client.api(f"orgs/{organization}/actions/permissions"))
        enabled_repositories = str(policy.get("enabled_repositories", "all"))
        if enabled_repositories == "selected":
            repository_data = cast(
                dict[str, Any], self._client.api(f"repos/{organization}/{repository}")
            )
            self._client.api(
                f"orgs/{organization}/actions/permissions/repositories/{repository_data['id']}",
                method="PUT",
            )
            return
        if enabled_repositories == "none":
            raise RuntimeError("organization policy disables GitHub Actions for all repositories")
        self._client.api(
            f"repos/{organization}/{repository}/actions/permissions",
            method="PUT",
            data={"enabled": True, "allowed_actions": "all"},
        )

    def _project_number(self, title: str) -> int:
        projects = cast(
            dict[str, Any],
            self._client.command_json(
                [
                    "project",
                    "list",
                    "--owner",
                    self._organization(),
                    "--limit",
                    "100",
                    "--format",
                    "json",
                ]
            ),
        )
        project = next(item for item in projects["projects"] if item["title"] == title)
        return int(project["number"])

    def _project_details(self, number: int) -> dict[str, Any]:
        response = cast(
            dict[str, Any],
            self._client.graphql(
                _PROJECT_BY_NUMBER_QUERY,
                {"organization": self._organization(), "number": number},
            ),
        )
        return cast(dict[str, Any], response["data"]["organization"]["projectV2"])

    def _organization(self) -> str:
        if self.organization is None:
            raise RuntimeError("GitHub preflight has not selected an organization")
        return self.organization


_PROJECT_QUERY = """
query PlatformForgeProjects($organization: String!) {
  organization(login: $organization) {
    projectsV2(first: 100) {
      nodes {
        id number title shortDescription public
        fields(first: 100) {
          nodes {
            ... on ProjectV2SingleSelectField {
              id name options { id name color description }
            }
          }
        }
        repositories(first: 100) { nodes { name } }
      }
    }
  }
}
"""

_PROJECT_BY_NUMBER_QUERY = """
query PlatformForgeProject($organization: String!, $number: Int!) {
  organization(login: $organization) {
    projectV2(number: $number) {
      id number title
      fields(first: 100) {
        nodes {
          ... on ProjectV2SingleSelectField {
            id name options { id name color description }
          }
        }
      }
    }
  }
}
"""

_UPDATE_FIELD_MUTATION = """
mutation PlatformForgeUpdateField(
  $fieldId: ID!
  $name: String!
  $options: [ProjectV2SingleSelectFieldOptionInput!]
) {
  updateProjectV2Field(
    input: {fieldId: $fieldId, name: $name, singleSelectOptions: $options}
  ) { projectV2Field { ... on ProjectV2SingleSelectField { id name } } }
}
"""
