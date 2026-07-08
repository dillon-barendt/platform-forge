# Platform Forge

Platform Forge is a deterministic scaffolding tool for modern Python platform
architectures.

```bash
uvx platform-forge new gateway
```

Platform Forge is not a generic AI code generator. It captures proven platform
architecture patterns and emits deterministic repositories from validated
Pydantic configuration.

The optional AI integration is only an architectural translator: it can map a
developer's domain description into `GatewayScaffoldConfig`, but it never
generates application source code or business logic. If AI is not installed or
configured, the CLI falls back to manual flags and interactive prompts.

Generated projects are portable. Their root `Makefile` is the canonical local
interface for install, dev, test, lint, format, typecheck, Redis, and doctor
workflows, so the scaffold remains maintainable without Platform Forge.

## Development

```bash
uv sync --extra dev --extra docs
uv run platform-forge --help
uv run platform-forge doctor
uv run pytest
```
