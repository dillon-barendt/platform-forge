# Platform Forge

Platform Forge is a deterministic scaffolding tool for modern Python platform
architectures.

```bash
uvx platform-forge new gateway
```

The AI integration is optional and only produces validated configuration. Source
files are generated from local Cookiecutter templates and remain maintainable
without Platform Forge after generation.

## Development

```bash
uv sync --extra dev --extra docs
uv run platform-forge --help
uv run platform-forge doctor
uv run pytest
```
