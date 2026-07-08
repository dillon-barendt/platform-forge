"""Default scaffold values used by CLI and non-AI fallback paths."""

DEFAULT_PROJECT_NAME = "gateway-platform"
DEFAULT_DOMAIN = "platform"
DEFAULT_PROVIDERS = ["example-provider"]
DEFAULT_SERVICES = ["pricing", "inventory", "fulfillment"]

FRONTEND_CHOICES = {"none", "vite", "nextjs"}
EVENT_BUS_CHOICES = {"none", "redis", "nats", "kafka"}
OBSERVABILITY_CHOICES = {"none", "logfire", "opentelemetry"}
