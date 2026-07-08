"""Provider adapter registry."""

from {{ cookiecutter.gateway_package }}.models import ProviderInfo

PROVIDERS: tuple[ProviderInfo, ...] = (
{{ cookiecutter.provider_entries }}
)
