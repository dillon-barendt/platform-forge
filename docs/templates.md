# Template System

This document provides an overview of the Platform Forge template system.

## Overview

Platform Forge uses a template-based approach to generate new projects. Templates are written in a simple, declarative
language and can be customized to your specific needs.

## Template Structure

A Platform Forge template is a directory that contains the following files:

- **`cookiecutter.json`:** A JSON file that defines the variables that can be used in the template.
- **`{{cookiecutter.project_slug}}`:** A directory that contains the files to be generated.

## Template Variables

The following variables are available in a Platform Forge template:

- **`scaffold_config`:** The full scaffold configuration.
- **`project_name`:** The human-readable name of the project.
- **`project_slug`:** The filesystem-safe name of the project.
- **`package_name`:** The Python package name of the project.
- **`gateway_package`:** The name of the gateway package.
- **`domain`:** The business domain of the project.
- **`providers`:** A list of external providers to integrate with.
- **`services`:** A list of internal services to integrate with.
- **`auth_strategy`:** The authentication strategy to use.
- **`event_bus`:** The event bus to use.
- **`frontend`:** The frontend framework to use.
- **`frontend_enabled`:** Whether the frontend is enabled.
- **`observability`:** The observability provider to use.

## Creating a Template

To create a new template, simply create a new directory with the structure described above. You can then use the
`platform-forge new` command to generate a new project from your template.
