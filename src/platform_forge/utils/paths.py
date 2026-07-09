"""Path and small input parsing helpers."""

from collections.abc import Iterable


def split_csv(value: str | Iterable[str] | None) -> list[str]:
    """Split comma-separated CLI input into non-empty items."""
    if value is None:
        return []
    if isinstance(value, str):
        items = value.split(",")
    else:
        items = [item for s in value for item in s.split(",")]
    return [item.strip() for item in items if item.strip()]
