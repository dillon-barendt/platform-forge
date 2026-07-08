"""Template registry abstraction."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path


@dataclass(frozen=True)
class TemplateRef:
    """Reference to a scaffold template."""

    scaffold_type: str
    path: Path
    source: str = "local"


class TemplateRegistry:
    """Registry for resolving scaffold templates."""

    def __init__(self, templates_root: Path | None = None) -> None:
        self._templates_root = templates_root

    def get_template(self, scaffold_type: str) -> TemplateRef:
        if scaffold_type != "gateway":
            msg = f"Unsupported scaffold type: {scaffold_type}"
            raise KeyError(msg)

        if self._templates_root is not None:
            template_path = self._templates_root / scaffold_type
        else:
            template_path = Path(
                str(files("platform_forge.templates") / "cookiecutters" / scaffold_type)
            )

        if not template_path.exists():
            msg = f"Template not found: {template_path}"
            raise FileNotFoundError(msg)

        return TemplateRef(scaffold_type=scaffold_type, path=template_path)
