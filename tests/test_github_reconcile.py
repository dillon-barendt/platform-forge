from collections.abc import Sequence

import pytest

from platform_forge.github.config import GitHubGovernanceConfig
from platform_forge.github.reconcile import (
    ApplyResult,
    GovernanceApplier,
    GovernancePlanner,
    LabelState,
    OrganizationSnapshot,
    PlannedOperation,
    ProjectState,
    RepositoryState,
    RulesetState,
    TeamState,
    desired_ruleset_payload,
)


def configured_governance() -> GitHubGovernanceConfig:
    return GitHubGovernanceConfig(
        organization="example-org",
        repositories=["api"],
        topics=["python", "platform-engineering"],
        teams=[
            {
                "slug": "maintainers",
                "description": "Repository maintainers",
                "permission": "maintain",
                "members": ["octocat"],
            }
        ],
        labels=[
            {"name": "type: bug", "color": "D73A4A", "description": "Bug"},
        ],
        release={"repositories": ["api"]},
    )


def test_plan_creates_every_missing_managed_resource() -> None:
    config = configured_governance()
    snapshot = OrganizationSnapshot(
        repositories={"api": RepositoryState(name="api")},
    )

    operations = GovernancePlanner(config, snapshot).build()
    actions = {(operation.resource, operation.target): operation.action for operation in operations}

    assert actions[("team", "maintainers")] == "create"
    assert actions[("team member", "maintainers/octocat")] == "create"
    assert actions[("repository permission", "maintainers/api")] == "create"
    assert actions[("label", "api:type: bug")] == "create"
    assert actions[("topics", "api")] == "update"
    assert actions[("project", "Roadmap")] == "create"
    assert actions[("project field", "Roadmap:Status")] == "create"
    assert actions[("project link", "Roadmap:api")] == "create"
    assert actions[("ruleset", "Platform Forge default branch")] == "create"
    assert actions[("workflow permissions", "api")] == "update"


def test_plan_preserves_unmanaged_labels_topics_and_project_options() -> None:
    config = configured_governance()
    snapshot = OrganizationSnapshot(
        repositories={
            "api": RepositoryState(
                name="api",
                labels={
                    "custom": LabelState(color="ABCDEF", description="Keep"),
                    "type: bug": LabelState(color="000000", description="Old"),
                },
                topics={"existing-topic", "python"},
            )
        },
        project=ProjectState(
            title="Roadmap",
            description=config.project.description,
            visibility=config.project.visibility,
            fields={
                "Status": {"Icebox", "Backlog", "Ready", "In Progress", "In Review", "Done"},
                "Priority": {"P0", "P1", "P2", "P3"},
                "Size": {"XS", "S", "M", "L"},
            },
            linked_repositories={"api"},
        ),
    )

    operations = GovernancePlanner(config, snapshot).build()
    label_operation = next(operation for operation in operations if operation.resource == "label")
    topics_operation = next(operation for operation in operations if operation.resource == "topics")
    status_operation = next(
        operation
        for operation in operations
        if operation.resource == "project field" and operation.target.endswith(":Status")
    )

    assert label_operation.action == "update"
    assert label_operation.payload["name"] == "type: bug"
    assert topics_operation.payload["topics"] == [
        "existing-topic",
        "platform-engineering",
        "python",
    ]
    assert status_operation.action == "unchanged"
    assert all(operation.target != "api:custom" for operation in operations)


def test_matching_snapshot_produces_only_unchanged_operations() -> None:
    config = configured_governance()
    snapshot = OrganizationSnapshot(
        repositories={
            "api": RepositoryState(
                name="api",
                labels={"type: bug": LabelState(color="D73A4A", description="Bug")},
                topics={"python", "platform-engineering"},
                workflow_permissions=("read", True),
            )
        },
        teams={
            "maintainers": TeamState(
                description="Repository maintainers",
                privacy="closed",
                members={"octocat"},
                repository_permissions={"api": "maintain"},
            )
        },
        project=ProjectState(
            title="Roadmap",
            description=config.project.description,
            visibility="PRIVATE",
            fields={field.name: set(field.options) for field in config.project.fields},
            linked_repositories={"api"},
        ),
        ruleset=RulesetState(payload=desired_ruleset_payload(config)),
    )

    operations = GovernancePlanner(config, snapshot).build()

    assert operations
    assert {operation.action for operation in operations} == {"unchanged"}


def test_wildcard_plan_rejects_release_repository_that_was_not_resolved() -> None:
    config = GitHubGovernanceConfig(
        organization="example-org",
        repositories=["*"],
        teams=[],
        labels=[],
        topics=[],
        project={"fields": []},
        release={"repositories": ["missing"]},
    )
    snapshot = OrganizationSnapshot(
        repositories={"api": RepositoryState(name="api")},
    )

    with pytest.raises(ValueError, match="release repositories were not found: missing"):
        GovernancePlanner(config, snapshot).build()


class RecordingExecutor:
    def __init__(self, fail_target: str | None = None) -> None:
        self.fail_target = fail_target
        self.executed: list[str] = []

    def execute(self, operation: PlannedOperation) -> None:
        target = operation.target
        self.executed.append(target)
        if target == self.fail_target:
            raise RuntimeError("policy blocked this change")


def mutation_targets(results: Sequence[ApplyResult]) -> list[str]:
    return [result.target for result in results if result.action not in {"unchanged", "skipped"}]


def test_apply_stops_after_failure_and_reports_skipped_mutations() -> None:
    config = configured_governance()
    snapshot = OrganizationSnapshot(
        repositories={"api": RepositoryState(name="api")},
    )
    operations = GovernancePlanner(config, snapshot).build()
    executor = RecordingExecutor(fail_target="maintainers/octocat")

    results = GovernanceApplier(executor).apply(operations)

    failed = next(result for result in results if result.action == "failed")
    assert failed.target == "maintainers/octocat"
    assert "policy blocked" in failed.detail
    assert any(result.action == "skipped" for result in results)
    assert executor.executed == mutation_targets(results)
