.PHONY: install dev dev-gateway dev-web redis test lint format typecheck doctor

install:
	uv sync --all-packages --all-extras --all-groups
{% if cookiecutter.frontend_enabled %}
	@if command -v pnpm >/dev/null 2>&1; then cd apps/web && pnpm install --config.dangerouslyAllowAllBuilds=true; else echo "pnpm not found; skipping web install"; fi
{% endif %}

dev:
	$(MAKE) redis
	$(MAKE) dev-gateway

dev-gateway:
	uv run --all-packages fastapi dev apps/gateway/src/{{ cookiecutter.gateway_package }}/main.py

dev-web:
{% if cookiecutter.frontend_enabled %}
	cd apps/web && pnpm dev
{% else %}
	@echo "No frontend scaffold was generated."
{% endif %}

redis:
	docker compose up -d redis

test:
	uv run --all-packages pytest

lint:
	uv run --all-packages ruff check .

format:
	uv run --all-packages ruff format .

typecheck:
	uv run --all-packages mypy apps/gateway/src

doctor:
	uv run --all-packages python -m {{ cookiecutter.gateway_package }}.doctor
