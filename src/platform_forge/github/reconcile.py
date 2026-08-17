"""Pure planning and fail-safe application for GitHub governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from platform_forge.github.config import GitHubGovernanceConfig

OperationAction = Literal["create", "update", "unchanged", "skipped", "failed"]


@dataclass(frozen=True)
class LabelState:
    """Observed label properties."""

    color: str
    description: str


@dataclass(frozen=True)
class RepositoryState:
    """Observed repository governance state."""

    name: str
    labels: dict[str, LabelState] = field(default_factory=dict)
    topics: set[str] = field(default_factory=set)
    workflow_permissions: tuple[str, bool] = ("read", False)


@dataclass(frozen=True)
class TeamState:
    """Observed team, membership, and repository access."""

    description: str
    privacy: str
    members: set[str] = field(default_factory=set)
    repository_permissions: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ProjectState:
    """Observed organization project state."""

    title: str
    description: str
    visibility: str
    fields: dict[str, set[str]] = field(default_factory=dict)
    linked_repositories: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class RulesetState:
    """Observed ruleset represented by its canonical API payload."""

    payload: dict[str, Any]


@dataclass(frozen=True)
class OrganizationSnapshot:
    """Read-only state used to calculate a deterministic plan."""

    repositories: dict[str, RepositoryState]
    teams: dict[str, TeamState] = field(default_factory=dict)
    project: ProjectState | None = None
    ruleset: RulesetState | None = None


@dataclass(frozen=True)
class PlannedOperation:
    """One observable governance decision."""

    action: OperationAction
    resource: str
    target: str
    detail: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ApplyResult:
    """Outcome of one planned operation."""

    action: OperationAction
    resource: str
    target: str
    detail: str


class OperationExecutor(Protocol):
    """Boundary implemented by the live GitHub gateway."""

    def execute(self, operation: PlannedOperation) -> None: ...


def desired_ruleset_payload(config: GitHubGovernanceConfig) -> dict[str, Any]:
    """Build the canonical organization ruleset payload."""
    repository_names = ["~ALL"] if config.repositories == ["*"] else config.repositories
    rules: list[dict[str, Any]] = [
        {"type": "deletion"},
        {"type": "non_fast_forward"},
        {
            "type": "pull_request",
            "parameters": {
                "dismiss_stale_reviews_on_push": False,
                "require_code_owner_review": False,
                "require_last_push_approval": False,
                "required_approving_review_count": config.ruleset.required_approvals,
                "required_review_thread_resolution": True,
            },
        },
    ]
    if config.ruleset.required_status_checks:
        rules.append(
            {
                "type": "required_status_checks",
                "parameters": {
                    "do_not_enforce_on_create": False,
                    "required_status_checks": [
                        {"context": check} for check in config.ruleset.required_status_checks
                    ],
                    "strict_required_status_checks_policy": True,
                },
            }
        )
    return {
        "name": config.ruleset.name,
        "target": "branch",
        "enforcement": config.ruleset.enforcement,
        "conditions": {
            "repository_name": {
                "include": repository_names,
                "exclude": [],
                "protected": False,
            },
            "ref_name": {"include": ["~DEFAULT_BRANCH"], "exclude": []},
        },
        "rules": rules,
        "bypass_actors": [],
    }


class GovernancePlanner:
    """Compare desired configuration with a read-only organization snapshot."""

    def __init__(
        self,
        config: GitHubGovernanceConfig,
        snapshot: OrganizationSnapshot,
    ) -> None:
        self._config = config
        self._snapshot = snapshot

    def _selected_repositories(self) -> list[str]:
        if self._config.repositories == ["*"]:
            repositories = sorted(self._snapshot.repositories)
        else:
            repositories = self._config.repositories
        missing = set(repositories) - self._snapshot.repositories.keys()
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"selected repositories were not found: {names}")
        missing_release = set(self._config.release.repositories) - set(repositories)
        if missing_release:
            names = ", ".join(sorted(missing_release))
            raise ValueError(f"release repositories were not found: {names}")
        return repositories

    def build(self) -> list[PlannedOperation]:
        """Return all create, update, and unchanged decisions."""
        repositories = self._selected_repositories()
        operations: list[PlannedOperation] = []
        operations.extend(self._plan_teams(repositories))
        operations.extend(self._plan_repositories(repositories))
        operations.extend(self._plan_project(repositories))
        operations.append(self._plan_ruleset())
        operations.extend(self._plan_workflow_permissions())
        return operations

    def _plan_teams(self, repositories: list[str]) -> list[PlannedOperation]:
        operations: list[PlannedOperation] = []
        for desired in self._config.teams:
            current = self._snapshot.teams.get(desired.slug)
            team_payload = desired.model_dump(mode="json")
            team_payload.pop("members")
            if current is None:
                action: OperationAction = "create"
            elif current.description != desired.description or current.privacy != desired.privacy:
                action = "update"
            else:
                action = "unchanged"
            operations.append(
                PlannedOperation(
                    action=action,
                    resource="team",
                    target=desired.slug,
                    detail="team settings",
                    payload=team_payload,
                )
            )

            current_members = current.members if current else set()
            for member in desired.members:
                operations.append(
                    PlannedOperation(
                        action="unchanged" if member in current_members else "create",
                        resource="team member",
                        target=f"{desired.slug}/{member}",
                        detail="team membership",
                        payload={"team": desired.slug, "member": member, "role": "member"},
                    )
                )

            current_permissions = current.repository_permissions if current else {}
            for repository in repositories:
                permission = current_permissions.get(repository)
                if permission is None:
                    permission_action: OperationAction = "create"
                elif permission != desired.permission:
                    permission_action = "update"
                else:
                    permission_action = "unchanged"
                operations.append(
                    PlannedOperation(
                        action=permission_action,
                        resource="repository permission",
                        target=f"{desired.slug}/{repository}",
                        detail=f"{desired.permission} access",
                        payload={
                            "team": desired.slug,
                            "repository": repository,
                            "permission": desired.permission,
                        },
                    )
                )
        return operations

    def _plan_repositories(self, repositories: list[str]) -> list[PlannedOperation]:
        operations: list[PlannedOperation] = []
        for repository in repositories:
            current = self._snapshot.repositories[repository]
            for desired in self._config.labels:
                label = current.labels.get(desired.name)
                if label is None:
                    action: OperationAction = "create"
                elif (
                    label.color.upper() != desired.color.upper()
                    or label.description != desired.description
                ):
                    action = "update"
                else:
                    action = "unchanged"
                operations.append(
                    PlannedOperation(
                        action=action,
                        resource="label",
                        target=f"{repository}:{desired.name}",
                        detail="managed label",
                        payload={"repository": repository, **desired.model_dump(mode="json")},
                    )
                )

            topics = current.topics | set(self._config.topics)
            operations.append(
                PlannedOperation(
                    action="unchanged" if topics == current.topics else "update",
                    resource="topics",
                    target=repository,
                    detail="preserve existing topics and add managed topics",
                    payload={"repository": repository, "topics": sorted(topics)},
                )
            )
        return operations

    def _plan_project(self, repositories: list[str]) -> list[PlannedOperation]:
        desired = self._config.project
        current = self._snapshot.project
        if current is None:
            project_action: OperationAction = "create"
        elif current.description != desired.description or current.visibility != desired.visibility:
            project_action = "update"
        else:
            project_action = "unchanged"
        operations = [
            PlannedOperation(
                action=project_action,
                resource="project",
                target=desired.title,
                detail="organization project",
                payload={
                    "title": desired.title,
                    "description": desired.description,
                    "visibility": desired.visibility,
                },
            )
        ]

        current_fields = current.fields if current else {}
        for desired_field in desired.fields:
            existing_options = current_fields.get(desired_field.name)
            action: OperationAction
            if existing_options is None:
                action = "create"
                options = desired_field.options
            elif set(desired_field.options).issubset(existing_options):
                action = "unchanged"
                options = sorted(existing_options)
            else:
                action = "update"
                options = [
                    *desired_field.options,
                    *sorted(existing_options - set(desired_field.options)),
                ]
            operations.append(
                PlannedOperation(
                    action=action,
                    resource="project field",
                    target=f"{desired.title}:{desired_field.name}",
                    detail="single-select project field",
                    payload={
                        "project": desired.title,
                        "name": desired_field.name,
                        "options": options,
                    },
                )
            )

        current_links = current.linked_repositories if current else set()
        for repository in repositories:
            operations.append(
                PlannedOperation(
                    action="unchanged" if repository in current_links else "create",
                    resource="project link",
                    target=f"{desired.title}:{repository}",
                    detail="project repository link",
                    payload={"project": desired.title, "repository": repository},
                )
            )
        return operations

    def _plan_ruleset(self) -> PlannedOperation:
        desired = desired_ruleset_payload(self._config)
        current = self._snapshot.ruleset
        if current is None:
            action: OperationAction = "create"
        elif current.payload != desired:
            action = "update"
        else:
            action = "unchanged"
        return PlannedOperation(
            action=action,
            resource="ruleset",
            target=self._config.ruleset.name,
            detail="lean active default-branch protection",
            payload=desired,
        )

    def _plan_workflow_permissions(self) -> list[PlannedOperation]:
        operations: list[PlannedOperation] = []
        for repository in self._config.release.repositories:
            current = self._snapshot.repositories[repository].workflow_permissions
            operations.append(
                PlannedOperation(
                    action="unchanged" if current == ("read", True) else "update",
                    resource="workflow permissions",
                    target=repository,
                    detail=(
                        "security-sensitive: keep default token read-only and allow Actions "
                        "to create or approve pull requests"
                    ),
                    payload={
                        "repository": repository,
                        "default_workflow_permissions": "read",
                        "can_approve_pull_request_reviews": True,
                    },
                )
            )
        return operations


class GovernanceApplier:
    """Execute a reviewed plan, stopping safely after the first failure."""

    def __init__(self, executor: OperationExecutor) -> None:
        self._executor = executor

    def apply(self, operations: list[PlannedOperation]) -> list[ApplyResult]:
        results: list[ApplyResult] = []
        failed = False
        for operation in operations:
            if operation.action == "unchanged":
                results.append(
                    ApplyResult(
                        action="unchanged",
                        resource=operation.resource,
                        target=operation.target,
                        detail=operation.detail,
                    )
                )
                continue
            if failed:
                results.append(
                    ApplyResult(
                        action="skipped",
                        resource=operation.resource,
                        target=operation.target,
                        detail="not attempted after an earlier failure",
                    )
                )
                continue
            try:
                self._executor.execute(operation)
            except Exception as exc:  # executor errors are reported as partial apply results
                failed = True
                results.append(
                    ApplyResult(
                        action="failed",
                        resource=operation.resource,
                        target=operation.target,
                        detail=str(exc),
                    )
                )
            else:
                results.append(
                    ApplyResult(
                        action=operation.action,
                        resource=operation.resource,
                        target=operation.target,
                        detail=operation.detail,
                    )
                )
        return results
