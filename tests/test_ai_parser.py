import pytest

from platform_forge.ai import AIUnavailableError, DomainConfigParser
from platform_forge.core.models import GatewayScaffoldConfig, WorkspaceConfig


class FakeResult:
    output = GatewayScaffoldConfig(
        workspace=WorkspaceConfig(project_name="Ticket Platform", domain="ticketing")
    )


class FakeAgent:
    def run_sync(self, user_prompt: str) -> FakeResult:
        assert "tickets" in user_prompt
        return FakeResult()


def test_parser_uses_injected_agent() -> None:
    config = DomainConfigParser(agent=FakeAgent()).parse("Build a tickets platform")

    assert config.workspace.project_slug == "ticket-platform"


def test_parser_includes_baseline_when_provided() -> None:
    baseline = GatewayScaffoldConfig(
        workspace=WorkspaceConfig(project_name="Baseline Platform", domain="ticketing")
    )
    config = DomainConfigParser(agent=FakeAgent()).parse(
        "Build a tickets platform",
        baseline=baseline,
    )

    assert config.workspace.project_slug == "ticket-platform"


def test_parser_requires_agent_or_model() -> None:
    with pytest.raises(AIUnavailableError):
        DomainConfigParser().parse("Build a tickets platform")
