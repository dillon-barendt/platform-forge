.PHONY: install dev dev-gateway dev-web redis test lint format typecheck doctor

-include .env

PYTHON_SYNC := uv sync --all-packages
PNPM_INSTALL := pnpm install --config.dangerouslyAllowAllBuilds=true

install:
	$(PYTHON_SYNC)
{% if cookiecutter.frontend_enabled %}
	@if command -v pnpm >/dev/null 2>&1; then $(PNPM_INSTALL); else echo "pnpm not found; skipping web install"; fi
{% endif %}

dev:
	$(MAKE) redis
	$(PYTHON_SYNC)
{% if cookiecutter.frontend_enabled %}
	$(PNPM_INSTALL)
	uv run --all-packages fastapi dev apps/gateway/src/{{ cookiecutter.gateway_package }}/main.py & \
	GATEWAY_PID=$$!; \
	trap 'kill $$GATEWAY_PID' INT TERM EXIT; \
	pnpm --filter web run dev
{% else %}
	uv run --all-packages fastapi dev apps/gateway/src/{{ cookiecutter.gateway_package }}/main.py
{% endif %}

dev-gateway:
	uv run --all-packages fastapi dev apps/gateway/src/{{ cookiecutter.gateway_package }}/main.py

dev-web:
{% if cookiecutter.frontend_enabled %}
	pnpm --filter web run dev
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
