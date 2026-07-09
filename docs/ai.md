# AI Integration

This document provides an overview of the Platform Forge AI integration.

## Overview

Platform Forge can use an optional AI engine to generate the configuration for your platform from a natural language
description. This can be a great way to get started with a new project quickly, without having to worry about the
details of the configuration file.

## Usage

To use the AI integration, simply pass the `--from-description` option to the `platform-forge new gateway` command with
a natural language description of your project. For example:

```bash
platform-forge new gateway --from-description "A simple e-commerce platform with a Vite frontend, a Redis event bus, and Logfire for observability."
```

Platform Forge will then use the AI engine to generate a configuration file that matches your description. You can then
review and modify the configuration as needed.

## How it Works

The AI integration is powered by a large language model (LLM) that has been trained on a massive dataset of text and
code. When you provide a natural language description of your project, Platform Forge sends it to the LLM, which then
generates a configuration file that matches your description.

## Limitations

The AI integration is still under development and has some limitations. For example, it may not be able to understand
complex or ambiguous descriptions, and it may not be able to generate a configuration that is perfectly optimized for
your specific needs. However, it can be a great way to get started with a new project quickly, and it is constantly
being improved.
