"""Strict configuration for GitHub organization governance."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

RepositoryPermission = Literal["pull", "triage", "push", "maintain", "admin"]
TeamPrivacy = Literal["closed", "secret"]
RulesetEnforcement = Literal["active", "disabled", "evaluate"]
ProjectVisibility = Literal["PUBLIC", "PRIVATE"]

_SLUG_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
_TOPIC_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,49}$")
_COLOR_PATTERN = re.compile(r"^[0-9A-Fa-f]{6}$")


class GovernanceModel(BaseModel):
    """Base model that rejects misspelled or unsupported configuration."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class TeamConfig(GovernanceModel):
    """A managed organization team and its selected-repository access."""

    slug: str = Field(min_length=1)
    description: str = ""
    privacy: TeamPrivacy = "closed"
    permission: RepositoryPermission
    members: list[str] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        if not _SLUG_PATTERN.fullmatch(value):
            msg = "team slug must contain only letters, numbers, dots, dashes, or underscores"
            raise ValueError(msg)
        return value.lower()

    @field_validator("members")
    @classmethod
    def unique_members(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            msg = "team members must be unique"
            raise ValueError(msg)
        return value


class LabelConfig(GovernanceModel):
    """A managed issue and pull-request label."""

    name: str = Field(min_length=1)
    color: str
    description: str = ""

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        if not _COLOR_PATTERN.fullmatch(value):
            msg = "label color must be a six-character hexadecimal value"
            raise ValueError(msg)
        return value.upper()


class ProjectFieldConfig(GovernanceModel):
    """A single-select field on the managed organization project."""

    name: str = Field(min_length=1)
    options: list[str] = Field(min_length=1)

    @field_validator("options")
    @classmethod
    def unique_options(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            msg = "project field options must be unique"
            raise ValueError(msg)
        return value


def default_project_fields() -> list[ProjectFieldConfig]:
    return [
        ProjectFieldConfig(
            name="Status",
            options=["Backlog", "Ready", "In Progress", "In Review", "Done"],
        ),
        ProjectFieldConfig(name="Priority", options=["P0", "P1", "P2", "P3"]),
        ProjectFieldConfig(name="Size", options=["XS", "S", "M", "L"]),
    ]


class ProjectConfig(GovernanceModel):
    """The managed organization-level GitHub Project."""

    title: str = "Roadmap"
    description: str = "Organization roadmap managed by Platform Forge."
    visibility: ProjectVisibility = "PRIVATE"
    fields: list[ProjectFieldConfig] = Field(default_factory=default_project_fields)

    @model_validator(mode="after")
    def unique_field_names(self) -> ProjectConfig:
        names = [field.name for field in self.fields]
        if len(names) != len(set(names)):
            msg = "project field names must be unique"
            raise ValueError(msg)
        return self


class RulesetConfig(GovernanceModel):
    """Lean default-branch protection applied at organization level."""

    name: str = "Platform Forge default branch"
    enforcement: RulesetEnforcement = "active"
    required_approvals: int = Field(default=1, ge=0, le=10)
    required_status_checks: list[str] = Field(default_factory=list)

    @field_validator("required_status_checks")
    @classmethod
    def unique_checks(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            msg = "required status checks must be unique"
            raise ValueError(msg)
        return value


class ReleaseConfig(GovernanceModel):
    """Repositories prepared to let GitHub Actions open release pull requests."""

    repositories: list[str] = Field(default_factory=list)


def default_teams() -> list[TeamConfig]:
    return [
        TeamConfig(
            slug="platform-admins",
            description="Platform administrators",
            permission="admin",
        ),
        TeamConfig(
            slug="maintainers",
            description="Repository maintainers",
            permission="maintain",
        ),
        TeamConfig(
            slug="contributors",
            description="Project contributors",
            permission="push",
        ),
    ]


def default_labels() -> list[LabelConfig]:
    return [
        LabelConfig(name="type: bug", color="D73A4A", description="Something is not working"),
        LabelConfig(name="type: feature", color="0052CC", description="New capability"),
        LabelConfig(name="type: docs", color="0075CA", description="Documentation change"),
        LabelConfig(name="type: maintenance", color="5319E7", description="Maintenance work"),
        LabelConfig(name="priority: critical", color="B60205", description="Immediate attention"),
        LabelConfig(name="priority: high", color="D93F0B", description="High priority"),
        LabelConfig(name="priority: medium", color="FBCA04", description="Normal priority"),
        LabelConfig(name="priority: low", color="0E8A16", description="Low priority"),
        LabelConfig(name="good first issue", color="7057FF", description="Good for newcomers"),
        LabelConfig(name="help wanted", color="008672", description="Extra attention is welcome"),
    ]


class GitHubGovernanceConfig(GovernanceModel):
    """Single-organization governance configuration."""

    schema_version: Literal[1] = 1
    organization: str = Field(min_length=1)
    repositories: list[str] = Field(min_length=1)
    topics: list[str] = Field(default_factory=lambda: ["managed-by-platform-forge"])
    teams: list[TeamConfig] = Field(default_factory=default_teams)
    labels: list[LabelConfig] = Field(default_factory=default_labels)
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    ruleset: RulesetConfig = Field(default_factory=RulesetConfig)
    release: ReleaseConfig = Field(default_factory=ReleaseConfig)

    @field_validator("organization")
    @classmethod
    def validate_organization(cls, value: str) -> str:
        if not _SLUG_PATTERN.fullmatch(value):
            msg = "organization must be a GitHub login"
            raise ValueError(msg)
        return value

    @field_validator("repositories")
    @classmethod
    def validate_repositories(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            msg = "repositories must be unique"
            raise ValueError(msg)
        if "*" in value and len(value) != 1:
            msg = "repository wildcard must be used by itself"
            raise ValueError(msg)
        invalid = [name for name in value if name != "*" and not _SLUG_PATTERN.fullmatch(name)]
        if invalid:
            msg = f"invalid repository names: {', '.join(invalid)}"
            raise ValueError(msg)
        return value

    @field_validator("topics")
    @classmethod
    def validate_topics(cls, value: list[str]) -> list[str]:
        if len(value) != len(set(value)):
            msg = "topics must be unique"
            raise ValueError(msg)
        invalid = [topic for topic in value if not _TOPIC_PATTERN.fullmatch(topic)]
        if invalid:
            msg = f"invalid repository topics: {', '.join(invalid)}"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def validate_managed_resources(self) -> GitHubGovernanceConfig:
        team_slugs = [team.slug for team in self.teams]
        if len(team_slugs) != len(set(team_slugs)):
            msg = "team slugs must be unique"
            raise ValueError(msg)

        label_names = [label.name for label in self.labels]
        if len(label_names) != len(set(label_names)):
            msg = "label names must be unique"
            raise ValueError(msg)

        release_repositories = set(self.release.repositories)
        if self.repositories != ["*"] and not release_repositories.issubset(self.repositories):
            msg = "release repositories must be selected repositories"
            raise ValueError(msg)
        return self

    @classmethod
    def from_toml(cls, path: Path) -> GitHubGovernanceConfig:
        """Load and validate a governance configuration file."""
        with path.open("rb") as config_file:
            return cls.model_validate(tomllib.load(config_file))


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_array(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def render_config(config: GitHubGovernanceConfig) -> str:
    """Render deterministic TOML without adding a runtime writer dependency."""
    lines = [
        f"schema_version = {config.schema_version}",
        f"organization = {_toml_string(config.organization)}",
        f"repositories = {_toml_array(config.repositories)}",
        f"topics = {_toml_array(config.topics)}",
    ]
    for team in config.teams:
        lines.extend(
            [
                "",
                "[[teams]]",
                f"slug = {_toml_string(team.slug)}",
                f"description = {_toml_string(team.description)}",
                f"privacy = {_toml_string(team.privacy)}",
                f"permission = {_toml_string(team.permission)}",
                f"members = {_toml_array(team.members)}",
            ]
        )
    for label in config.labels:
        lines.extend(
            [
                "",
                "[[labels]]",
                f"name = {_toml_string(label.name)}",
                f"color = {_toml_string(label.color)}",
                f"description = {_toml_string(label.description)}",
            ]
        )
    lines.extend(
        [
            "",
            "[project]",
            f"title = {_toml_string(config.project.title)}",
            f"description = {_toml_string(config.project.description)}",
            f"visibility = {_toml_string(config.project.visibility)}",
        ]
    )
    for field in config.project.fields:
        lines.extend(
            [
                "",
                "[[project.fields]]",
                f"name = {_toml_string(field.name)}",
                f"options = {_toml_array(field.options)}",
            ]
        )
    lines.extend(
        [
            "",
            "[ruleset]",
            f"name = {_toml_string(config.ruleset.name)}",
            f"enforcement = {_toml_string(config.ruleset.enforcement)}",
            f"required_approvals = {config.ruleset.required_approvals}",
            f"required_status_checks = {_toml_array(config.ruleset.required_status_checks)}",
            "",
            "[release]",
            f"repositories = {_toml_array(config.release.repositories)}",
            "",
        ]
    )
    return "\n".join(lines)


def write_starter_config(
    path: Path,
    *,
    organization: str,
    repositories: list[str],
    force: bool = False,
) -> Path:
    """Create a validated starter configuration without silent overwrites."""
    config = GitHubGovernanceConfig(
        organization=organization,
        repositories=repositories,
    )
    if path.exists() and not force:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_config(config), encoding="utf-8")
    return path
