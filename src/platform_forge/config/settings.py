"""Settings for Platform Forge itself."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ForgeSettings(BaseSettings):
    """Environment-driven settings for optional Platform Forge integrations."""

    model_config = SettingsConfigDict(env_prefix="PLATFORM_FORGE_", extra="ignore")

    ai_model: str | None = Field(default=None, description="Pydantic AI model identifier.")
