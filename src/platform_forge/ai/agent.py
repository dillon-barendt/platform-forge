"""Optional Pydantic AI parser for domain descriptions."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar, cast

from platform_forge.ai.prompts import AI_SYSTEM_PROMPT
from platform_forge.config.models import GatewayScaffoldConfig

T = TypeVar("T")


class AIUnavailableError(RuntimeError):
    """Raised when AI parsing is requested but not configured."""


class SyncRunResult(Protocol[T]):
    """Minimal protocol for Pydantic AI run results."""

    output: T


class SyncConfigAgent(Protocol):
    """Minimal protocol implemented by pydantic_ai.Agent."""

    def run_sync(self, user_prompt: str) -> SyncRunResult[GatewayScaffoldConfig]: ...


def create_pydantic_ai_agent(model: str) -> SyncConfigAgent:
    """Create a Pydantic AI agent that returns GatewayScaffoldConfig."""
    try:
        from pydantic_ai import Agent  # type: ignore[import-not-found]
    except ImportError as exc:
        msg = "Install platform-forge[ai] to enable AI-assisted configuration parsing."
        raise AIUnavailableError(msg) from exc

    return cast(
        SyncConfigAgent,
        Agent(model, output_type=GatewayScaffoldConfig, system_prompt=AI_SYSTEM_PROMPT),
    )


class DomainConfigParser:
    """Parse natural-language domain descriptions into validated config."""

    def __init__(self, agent: SyncConfigAgent | None = None, model: str | None = None) -> None:
        self._agent = agent
        self._model = model

    def parse(self, description: str) -> GatewayScaffoldConfig:
        if not description.strip():
            msg = "description must not be empty"
            raise ValueError(msg)

        agent = self._agent
        if agent is None:
            if self._model is None:
                msg = "AI parsing requires a configured model or injected agent."
                raise AIUnavailableError(msg)
            agent = create_pydantic_ai_agent(self._model)

        result: Any = agent.run_sync(description)
        output = result.output
        if isinstance(output, GatewayScaffoldConfig):
            return output
        return GatewayScaffoldConfig.model_validate(output)
