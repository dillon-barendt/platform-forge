# Development Guide

This document provides a guide for developing Platform Forge.

## Getting Started

To get started with developing Platform Forge, you'll need to have the following installed:

- Python 3.13 or later
- `uv`

Once you have these installed, you can clone the repository and install the dependencies:

```bash
git clone https://github.com/dillon-barendt/platform-forge.git
cd platform-forge
uv sync -e dev
```

## Running the Tests

To run the tests, use the following command:

```bash
pytest
```

## Building the Documentation

To build the documentation, use the following command:

```bash
mkdocs build
```

## Submitting a Pull Request

When you're ready to submit a pull request, please make sure that you have done the following:

- Run the tests and make sure they all pass.
- Build the documentation and make sure it builds without any errors.
- Add a descriptive title and a detailed description to your pull request.
- Add a changelog entry to the `changelog.md` file.
