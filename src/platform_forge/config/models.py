"""Strongly typed scaffold configuration models."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Slug = str
FrontendFramework = Literal["none", "vite", "nextjs"]
EventBusProvider = Literal["none", "redis", "nats", "kafka"]
ObservabilityProvider = Literal["none", "logfire", "opentelemetry"]


def normalize_slug(value: str) -> str:
    """Normalize user input into a deterministic lowercase slug."""
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    normalized = re.sub(r"-+", "-", normalized)
    if not normalized:
        msg = "value must contain at least one alphanumeric character"
        raise ValueError(msg)
    return normalized


def package_name_from_slug(slug: str) -> str:
    """Convert a filesystem slug into a Python package-safe name."""
    return slug.replace("-", "_")


class ForgeBaseModel(BaseModel):
    """Base model for strict configuration objects."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class WorkspaceConfig(ForgeBaseModel):
    """Top-level workspace metadata."""

    project_name: str = Field(min_length=1, description="Human-readable project name.")
    project_slug: Slug | None = Field(default=None, description="Filesystem-safe project slug.")
    package_name: str | None = Field(default=None, description="Python package base name.")
    domain: str = Field(default="platform", min_length=1)

    @field_validator("project_slug", mode="before")
    @classmethod
    def normalize_project_slug(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_slug(value)

    @field_validator("package_name", mode="before")
    @classmethod
    def normalize_package_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return package_name_from_slug(normalize_slug(value))

    @model_validator(mode="after")
    def derive_names(self) -> WorkspaceConfig:
        slug = self.project_slug or normalize_slug(self.project_name)
        package_name = self.package_name or package_name_from_slug(slug)
        self.project_slug = slug
        self.package_name = package_name
        return self


class ProviderConfig(ForgeBaseModel):
    """External provider adapter to include in the generated gateway."""

    name: Slug
    display_name: str | None = None

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return normalize_slug(value)

    @model_validator(mode="after")
    def derive_display_name(self) -> ProviderConfig:
        self.display_name = self.display_name or self.name.replace("-", " ").title()
        return self


class InternalServiceConfig(ForgeBaseModel):
    """Internal service boundary represented by the gateway."""

    name: Slug
    port: int | None = Field(default=None, ge=1, le=65535)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return normalize_slug(value)


class AuthConfig(ForgeBaseModel):
    """Authentication settings for the scaffold."""

    strategy: Literal["none", "jwt", "oauth2"] = "jwt"


class EventBusConfig(ForgeBaseModel):
    """Event bus settings."""

    provider: EventBusProvider = "redis"


class FrontendConfig(ForgeBaseModel):
    """Frontend scaffold settings."""

    framework: FrontendFramework = "vite"

    @property
    def enabled(self) -> bool:
        return self.framework != "none"


class ObservabilityConfig(ForgeBaseModel):
    """Observability defaults."""

    provider: ObservabilityProvider = "logfire"


class GatewayScaffoldConfig(ForgeBaseModel):
    """Single source of truth for gateway scaffold generation."""

    workspace: WorkspaceConfig
    providers: list[ProviderConfig] = Field(default_factory=list)
    services: list[InternalServiceConfig] = Field(default_factory=list)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    event_bus: EventBusConfig = Field(default_factory=EventBusConfig)
    frontend: FrontendConfig = Field(default_factory=FrontendConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)

    @model_validator(mode="after")
    def require_unique_names(self) -> GatewayScaffoldConfig:
        provider_names = [provider.name for provider in self.providers]
        service_names = [service.name for service in self.services]
        if len(provider_names) != len(set(provider_names)):
            msg = "provider names must be unique"
            raise ValueError(msg)
        if len(service_names) != len(set(service_names)):
            msg = "service names must be unique"
            raise ValueError(msg)
        return self

    @classmethod
    def from_cli(
        cls,
        *,
        project_name: str,
        domain: str,
        providers: list[str],
        services: list[str],
        frontend: FrontendFramework,
        event_bus: EventBusProvider,
        observability: ObservabilityProvider,
    ) -> GatewayScaffoldConfig:
        return cls(
            workspace=WorkspaceConfig(project_name=project_name, domain=domain),
            providers=[ProviderConfig(name=name) for name in providers],
            services=[
                InternalServiceConfig(name=name, port=8100 + index)
                for index, name in enumerate(services)
            ],
            frontend=FrontendConfig(framework=frontend),
            event_bus=EventBusConfig(provider=event_bus),
            observability=ObservabilityConfig(provider=observability),
        )

    def to_cookiecutter_context(self) -> dict[str, Any]:
        """Serialize to a deterministic Cookiecutter context."""
        project_slug = self.workspace.project_slug
        package_name = self.workspace.package_name
        if project_slug is None or package_name is None:
            msg = "workspace names were not derived"
            raise ValueError(msg)

        return {
            "project_name": self.workspace.project_name,
            "project_slug": project_slug,
            "package_name": package_name,
            "gateway_package": f"{package_name}_gateway",
            "domain": self.workspace.domain,
            "providers": [provider.model_dump(mode="json") for provider in self.providers],
            "provider_entries": "\n".join(
                f'    ProviderInfo(name="{provider.name}", display_name="{provider.display_name}"),'
                for provider in self.providers
            ),
            "services": [service.model_dump(mode="json") for service in self.services],
            "service_entries": "\n".join(
                f'    ServiceInfo(name="{service.name}", port={service.port}),'
                for service in self.services
            ),
            "auth_strategy": self.auth.strategy,
            "event_bus": self.event_bus.provider,
            "frontend": self.frontend.framework,
            "frontend_enabled": self.frontend.enabled,
            "observability": self.observability.provider,
        }
