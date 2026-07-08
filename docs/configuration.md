# Configuration Reference

`GatewayScaffoldConfig` is the single source of truth for generated output.

It contains:

- `WorkspaceConfig`
- `ProviderConfig`
- `InternalServiceConfig`
- `AuthConfig`
- `EventBusConfig`
- `FrontendConfig`
- `ObservabilityConfig`

Generated projects use layered runtime configuration:

- root `.env` for shared infrastructure
- app-local `.env` files for runtime ownership
- Pydantic Settings for validation and defaults
- Makefile targets for orchestration
