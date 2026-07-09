# CLI Reference

This document provides a reference for the Platform Forge command-line interface.

## Global Options

- `--version`: Show the version and exit.
- `--help`: Show help and exit.

## `platform-forge new`

The `new` command is used to create a new project from a template.

### `platform-forge new gateway`

The `gateway` subcommand is used to create a new gateway project.

#### Options

- `--project-name`: The human-readable name of the project.
- `--domain`: The business domain of the project.
- `--providers`: A comma-separated list of external providers to integrate with.
- `--services`: A comma-separated list of internal services to integrate with.
- `--frontend`: The frontend framework to use.
- `--event-bus`: The event bus to use.
- `--observability`: The observability provider to use.
- `--interactive`: Prompt for missing options.
- `--output-dir`: The directory to create the project in.
- `--from-description`: A natural language description of the project.

## `platform-forge doctor`

The `doctor` command is used to check the health of your Platform Forge installation.
