"""Utility functions for working with strings."""

from __future__ import annotations

import re
from collections.abc import Iterable


def normalize_slug(value: str) -> str:
    """Normalize user input into a deterministic lowercase slug."""
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    normalized = re.sub(r"-+", "-", normalized)
    if not normalized:
        msg = "value must contain at least one alphanumeric character"
        raise ValueError(msg)
    return normalized


def package_name_from_slug(slug: str) -> str:
    """Convert a filesystem slug into a Python package-safe name."""
    return slug.replace("-", "_")


def split_csv(value: str | Iterable[str] | None) -> list[str]:
    """Split comma-separated CLI input into non-empty items."""
    if value is None:
        return []
    if isinstance(value, str):
        items = value.split(",")
    else:
        items = [item for s in value for item in s.split(",")]
    return [item.strip() for item in items if item.strip()]
