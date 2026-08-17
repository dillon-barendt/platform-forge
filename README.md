# Platform Forge

**Deterministic scaffolding for modern Python platform architectures.**

[![PyPI version](https://badge.fury.io/py/platform-forge.svg)](https://badge.fury.io/py/platform-forge)
[![Build status](https://github.com/dillon-barendt/platform-forge/actions/workflows/ci.yml/badge.svg)](https://github.com/dillon-barendt/platform-forge/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Platform Forge is a command-line tool that helps you create and manage modern Python platforms with a consistent and
well-defined structure. It uses a combination of templates, configuration, and optional AI-powered code generation to
help you build robust and scalable platforms.

## Key Features

- **Deterministic Scaffolding:** Create new projects from a predefined template, ensuring consistency and best practices
  across your organization.
- **Configuration-driven:** Define your platform's components and their relationships in a simple, declarative
  configuration file.
- **AI-powered (Optional):** Use natural language to describe your platform and let Platform Forge generate the
  configuration for you.
- **Extensible:** Create your own templates and plugins to customize Platform Forge to your specific needs.
- **Built for Modern Python:** Leverages the latest Python features and best practices to help you build high-quality
  platforms.
- **GitHub Governance:** Preview and upsert a small organization's teams, labels, topics, Roadmap project, and default
  branch ruleset from one strict TOML file.

## Installation

Platform Forge is available on PyPI and can be installed with `pip`:

```bash
pip install platform-forge
```

## Usage

To create a new gateway project, use the `platform-forge new gateway` command:

```bash
platform-forge new gateway --project-name "My Awesome Platform"
```

This will create a new project in a directory called `my-awesome-platform` with a default configuration. You can then
customize the configuration to your specific needs.

### GitHub organization quickstart

Install and authenticate the GitHub CLI before using governance commands. A classic OAuth token needs `admin:org`,
`project`, and repository access; an equivalent fine-grained token must be able to administer the organization and the
selected repositories.

```bash
platform-forge github init-config \
  --organization example-org \
  --repository api \
  --repository web

# Read-only: validates access and shows create/update/unchanged operations.
platform-forge github plan --config platform-forge.github.toml

# Run only after reviewing the plan.
platform-forge github apply --config platform-forge.github.toml --yes
```

Apply is upsert-only. It does not delete unrelated teams, memberships, labels, topics, projects, fields, or rulesets. If
an operation fails, Platform Forge reports the completed mutation, the failure, and every later mutation it skipped;
fix the access or policy problem and rerun the same command.

To add protected-branch-compatible semantic releases to a Python repository:

```bash
platform-forge github init-release
```

This writes Release Please files into the local checkout for review. It does not edit a remote repository or publish a
release. Add the repository to `[release].repositories`, apply the governance config, and commit the generated files.
For release repositories, apply keeps the organization and repository token defaults read-only, enables Actions only
where selected, and explicitly prevents non-release repositories from creating or approving pull requests.

For more information on how to use Platform Forge, see
the [documentation](https://dillon-barendt.github.io/platform-forge/).

## Contributing

Contributions are welcome! Please see
the [Contributing Guide](https://github.com/dillon-barendt/platform-forge/blob/main/CONTRIBUTING.md) for more
information.

## License

Platform Forge is licensed under the [MIT License](https://opensource.org/licenses/MIT).
