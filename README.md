# atext.ai

atext is a cert-auth, team-scoped A2UI presentation spine for agent teams.
Team agents authenticate with AWID team certificates, co-author plain text,
search the live web through the server-side LinkUp endpoint, store A2UI doc
views, and mint no-login `/present/<token>` links for humans.

## Product path

- `server/` — FastAPI relying party on `:8200`.
  - `POST /v1/documents` and `POST /v1/documents/{slug}/versions`
  - `POST /v1/search` — cert-auth LinkUp search; `LINKUP_API_KEY` stays on the server
  - `POST /v1/artifacts` — store A2UI doc views
  - `POST /v1/present` — mint public capability links
  - `GET /present/{token}` — public read for the frontend renderer
- `src/app/present/[token]` — the human surface. It fetches the public token
  response and renders A2UI with `@copilotkit/a2ui-renderer`.
- `agent/` — retired LangGraph/AG-UI concierge sidecar. Agents now call the
  server directly with `aw id request --team-auth`.

## Run locally

```bash
# server
cd server
GENUI_SERVER_DATABASE_URL=postgresql://localhost/genui \
GENUI_SERVER_PUBLIC_ORIGIN=http://127.0.0.1:8200 \
GENUI_SERVER_PRESENTATION_ORIGIN=http://127.0.0.1:3000 \
LINKUP_API_KEY=<real key> \
uv run uvicorn atext.api:app --host 127.0.0.1 --port 8200

# frontend
cd ..
SERVER_ORIGIN=http://127.0.0.1:8200 pnpm dev:ui --hostname 127.0.0.1 --port 3000
```

For the recordable flow, see `docs/demo-runbook.md`. For source of truth and
team-isolation rules, see `docs/sot.md`.

## Tests

```bash
cd server
uv run pytest
uv run ruff check .
uv run mypy src
```
