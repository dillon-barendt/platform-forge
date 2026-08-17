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

## `platform-forge github`

GitHub commands manage one organization at a time. They use your authenticated `gh` session and never read credentials
from the governance file.

### `platform-forge github init-config`

Create a strict starter `platform-forge.github.toml`:

```bash
platform-forge github init-config \
  --organization example-org \
  --repository api \
  --repository web
```

Repeat `--repository` for each managed repository. Pass `--repository '*'` by itself to explicitly select every
accessible, non-archived repository. Existing output is preserved unless `--force` is supplied.

### `platform-forge github plan`

Validate authentication, permissions, configuration, and current GitHub state without changing anything:

```bash
platform-forge github plan --config platform-forge.github.toml
```

`--check` returns exit code 2 when create or update operations are pending, which makes it suitable for drift checks.
Authentication, access, configuration, and read failures return exit code 1.

### `platform-forge github apply`

Rebuild the plan and perform its upserts:

```bash
platform-forge github apply --config platform-forge.github.toml --yes
```

`--yes` is mandatory. Apply stops after the first failed mutation, reports subsequent mutations as skipped, and can be
rerun after the problem is corrected. It never performs strict synchronization or deletion.

### `platform-forge github init-release`

Add Release Please configuration to a local Python checkout:

```bash
platform-forge github init-release \
  --project-root . \
  --branch development
```

The branch and standard `src/<package>/__init__.py` version file are detected when unambiguous. Use `--version-file`
for a different layout. Existing Release Please files are preserved unless `--force` is supplied.
