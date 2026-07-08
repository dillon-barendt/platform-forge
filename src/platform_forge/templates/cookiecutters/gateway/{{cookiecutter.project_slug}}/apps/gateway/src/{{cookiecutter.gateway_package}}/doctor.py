"""Generated project doctor checks."""

from __future__ import annotations

import sys

from {{ cookiecutter.gateway_package }}.settings import get_settings


def main() -> int:
    settings = get_settings()
    print(f"app={settings.app_name}")
    print(f"python={sys.version.split()[0]}")
    print(f"event_bus={settings.event_bus.provider}")
    print(f"observability={settings.observability.provider}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
