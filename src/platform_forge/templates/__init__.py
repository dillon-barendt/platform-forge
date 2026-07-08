"""Template registry, generator, and bundled Cookiecutter assets."""

from platform_forge.templates.cookiecutter import ScaffoldGenerator
from platform_forge.templates.registry import TemplateRef, TemplateRegistry

__all__ = ["ScaffoldGenerator", "TemplateRef", "TemplateRegistry"]
