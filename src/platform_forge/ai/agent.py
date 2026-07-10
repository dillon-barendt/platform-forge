"""Optional Pydantic AI parser for domain descriptions."""

from __future__ import annotations

from typing import Any, Protocol, TypeVar, cast

from platform_forge.ai.prompts import AI_SYSTEM_PROMPT
from platform_forge.core.models import GatewayScaffoldConfig

T = TypeVar("T")


class AIUnavailableError(RuntimeError):
    """Raised when AI parsing is requested but not configured."""


class SyncRunResult(Protocol[T]):
    """Minimal protocol for Pydantic AI run results."""

    output: T


class SyncConfigAgent(Protocol):
    """Minimal protocol implemented by pydantic_ai.Agent."""

    def run_sync(self, user_prompt: str) -> SyncRunResult[GatewayScaffoldConfig]: ...


def create_pydantic_ai_agent(model: str | None) -> SyncConfigAgent:
    """Create a Pydantic AI agent that returns GatewayScaffoldConfig."""
    if model is None:
        msg = "AI parsing requires a configured model."
        raise AIUnavailableError(msg)
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
    """Parse natural-language domain descriptions into validated core."""

    def __init__(self, agent: SyncConfigAgent | None = None, model: str | None = None) -> None:
        self._agent = agent
        self._model = model

    def parse(
        self,
        description: str,
        baseline: GatewayScaffoldConfig | None = None,
    ) -> GatewayScaffoldConfig:
        if not description.strip():
            msg = "description must not be empty"
            raise ValueError(msg)

        agent = self._agent or create_pydantic_ai_agent(self._model)

        user_prompt = description
        if baseline is not None:
            user_prompt = (
                "Use this baseline validated configuration as the starting point. "
                "Only adjust structural scaffold fields that are supported by the schema.\n\n"
                f"Baseline JSON:\n{baseline.model_dump_json(indent=2)}\n\n"
                f"Developer description:\n{description}"
            )

        result: Any = agent.run_sync(user_prompt)
        output = result.output
        if isinstance(output, GatewayScaffoldConfig):
            return output
        return GatewayScaffoldConfig.model_validate(output)
