# Configuration Reference

This document provides a reference for the Platform Forge configuration file.

## `pyproject.toml`

The `pyproject.toml` file is the main configuration file for a Platform Forge project. It contains the following
sections:

### `[project]`

This section contains metadata about the project, such as the name, version, and dependencies.

### `[tool.platform-forge]`

This section contains the configuration for Platform Forge itself. It is used to define the components of your platform
and their relationships.

#### `workspace`

This section contains the configuration for the workspace, such as the project name, slug, and domain.

#### `providers`

This section contains a list of external providers to integrate with. Each provider has a name and an optional display
name.

#### `services`

This section contains a list of internal services to integrate with. Each service has a name and an optional port.

#### `auth`

This section contains the configuration for authentication, such as the strategy to use.

#### `event_bus`

This section contains the configuration for the event bus, such as the provider to use.

#### `frontend`

This section contains the configuration for the frontend, such as the framework to use.

#### `observability`

This section contains the configuration for observability, such as the provider to use.
