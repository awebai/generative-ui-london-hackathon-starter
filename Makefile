.PHONY: server test-server lint-server

server:
	cd server && uv run uvicorn atext.api:app --host 0.0.0.0 --port 8200

test-server:
	cd server && uv run pytest

lint-server:
	cd server && uv run ruff check src tests && uv run mypy src
