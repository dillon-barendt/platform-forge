"""Internal service registry."""

from {{ cookiecutter.gateway_package }}.models import ServiceInfo

SERVICES: tuple[ServiceInfo, ...] = (
{{ cookiecutter.service_entries }}
)
