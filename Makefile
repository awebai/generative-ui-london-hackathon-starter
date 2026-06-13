.PHONY: server test-server lint-server e2e e2e-up e2e-down

server:
	cd server && uv run uvicorn atext.api:app --host 0.0.0.0 --port 8200

test-server:
	cd server && uv run pytest

lint-server:
	cd server && uv run ruff check src tests && uv run mypy src

e2e:
	set -e; \
	trap 'docker compose -p genui-e2e -f $(CURDIR)/docker-compose.e2e.yml down -v --remove-orphans' EXIT; \
	docker compose -p genui-e2e -f $(CURDIR)/docker-compose.e2e.yml down -v --remove-orphans >/dev/null 2>&1 || true; \
	docker compose -p genui-e2e -f $(CURDIR)/docker-compose.e2e.yml up --build -d; \
	cd server && GENUI_E2E=1 uv run pytest -q -m e2e

e2e-up:
	docker compose -p genui-e2e -f $(CURDIR)/docker-compose.e2e.yml up --build -d

e2e-down:
	docker compose -p genui-e2e -f $(CURDIR)/docker-compose.e2e.yml down -v --remove-orphans
