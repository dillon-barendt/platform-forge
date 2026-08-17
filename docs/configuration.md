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

## `platform-forge.github.toml`

GitHub governance uses a separate file so organization administration is never mixed with application runtime
configuration. The schema is strict: unknown fields, duplicate managed names, invalid permissions, mixed wildcard and
named repository selection, and release repositories outside the selected set are rejected before GitHub is read.

Generate a complete starter file with `platform-forge github init-config`. Its main shape is:

```toml
schema_version = 1
organization = "example-org"
repositories = ["api", "web"]
topics = ["managed-by-platform-forge", "python"]

[[teams]]
slug = "platform-admins"
description = "Platform administrators"
privacy = "closed"
permission = "admin"
members = ["octocat"]

[[labels]]
name = "type: bug"
color = "D73A4A"
description = "Something is not working"

[project]
title = "Roadmap"
description = "Organization roadmap managed by Platform Forge."
visibility = "PRIVATE"

[[project.fields]]
name = "Status"
options = ["Backlog", "Ready", "In Progress", "In Review", "Done"]

[ruleset]
name = "Platform Forge default branch"
enforcement = "active"
required_approvals = 1
required_status_checks = []

[release]
repositories = ["api"]
```

The starter includes three teams (`platform-admins`, `maintainers`, and `contributors`), ten compact labels, and Status,
Priority, and Size project fields. Extra existing labels, topics, project options, and memberships are preserved.

Repositories in `[release].repositories` receive a security-sensitive repository setting: the default `GITHUB_TOKEN`
permission stays `read`, while GitHub Actions is allowed to create or approve pull requests. When organization Actions
is limited to selected repositories, apply adds only the release repositories to that allowlist. GitHub requires the
organization workflow policy to permit pull-request creation before a repository can opt in, so apply surfaces that
organization-level change and explicitly keeps every selected non-release repository opted out. This lets Release
Please open a release PR; an enterprise policy may forbid the setting, in which case apply reports the policy conflict
and stops.

Organization rulesets require GitHub Team or Enterprise. On an unsupported plan, `plan` and `apply` report the ruleset
as `skipped` and continue with the remaining upserts; they never replace it with weaker repository settings silently.
