from pathlib import Path

import pytest
from pydantic import ValidationError

from platform_forge.github.config import (
    GitHubGovernanceConfig,
    write_starter_config,
)


def test_starter_config_round_trips_with_small_team_defaults(tmp_path: Path) -> None:
    destination = tmp_path / "platform-forge.github.toml"

    write_starter_config(
        destination,
        organization="example-org",
        repositories=["api", "web"],
    )

    config = GitHubGovernanceConfig.from_toml(destination)
    assert config.organization == "example-org"
    assert config.repositories == ["api", "web"]
    assert [(team.slug, team.permission) for team in config.teams] == [
        ("platform-admins", "admin"),
        ("maintainers", "maintain"),
        ("contributors", "push"),
    ]
    assert config.project.title == "Roadmap"
    assert config.ruleset.required_approvals == 1


def test_starter_config_refuses_to_overwrite_existing_file(tmp_path: Path) -> None:
    destination = tmp_path / "platform-forge.github.toml"
    destination.write_text("keep me", encoding="utf-8")

    with pytest.raises(FileExistsError):
        write_starter_config(
            destination,
            organization="example-org",
            repositories=["api"],
        )

    assert destination.read_text(encoding="utf-8") == "keep me"


def test_config_rejects_unknown_fields(tmp_path: Path) -> None:
    destination = tmp_path / "platform-forge.github.toml"
    destination.write_text(
        "\n".join(
            [
                "schema_version = 1",
                'organization = "example-org"',
                'repositories = ["api"]',
                "unexpected = true",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError, match="unexpected"):
        GitHubGovernanceConfig.from_toml(destination)


def test_config_rejects_wildcard_mixed_with_named_repositories() -> None:
    with pytest.raises(ValidationError, match="wildcard"):
        GitHubGovernanceConfig(
            organization="example-org",
            repositories=["*", "api"],
        )


def test_config_rejects_duplicate_managed_resource_names() -> None:
    with pytest.raises(ValidationError, match="team slugs must be unique"):
        GitHubGovernanceConfig(
            organization="example-org",
            repositories=["api"],
            teams=[
                {"slug": "maintainers", "permission": "maintain"},
                {"slug": "maintainers", "permission": "push"},
            ],
        )


def test_release_repositories_must_be_selected() -> None:
    with pytest.raises(ValidationError, match="release repositories must be selected"):
        GitHubGovernanceConfig(
            organization="example-org",
            repositories=["api"],
            release={"repositories": ["web"]},
        )
