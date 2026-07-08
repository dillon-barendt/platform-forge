# Architecture

Platform Forge follows a narrow pipeline:

```text
Typer CLI
    -> interactive prompts / flags
    -> optional Pydantic AI config parsing
    -> GatewayScaffoldConfig
    -> Cookiecutter context
    -> deterministic project generation
```

The AI layer never writes source code. It only returns structured configuration.
