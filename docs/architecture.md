# Architecture

Platform Forge follows a narrow deterministic pipeline:

```text
Typer CLI
    -> interactive questionnaire and/or flags
    -> optional Pydantic AI architectural translation
    -> strict GatewayScaffoldConfig validation
    -> deterministic Cookiecutter context
    -> deterministic project generation
```

The AI layer never writes source code. It only returns structured configuration.

Generated projects are self-contained. Platform Forge may later provide wrapper
commands such as `platform-forge dev`, but those commands must delegate to the
generated project's own Makefile targets instead of duplicating orchestration.
