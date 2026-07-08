"""Path and small input parsing helpers."""

from collections.abc import Iterable


def split_csv(value: str | Iterable[str] | None) -> list[str]:
    """Split comma-separated CLI input into non-empty items."""
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = value.split(",")
    else:
        raw_items = []
        for item in value:
            raw_items.extend(item.split(","))
    return [item.strip() for item in raw_items if item.strip()]
