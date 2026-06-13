# Re-scoped GenUI deploy artifacts

Branch basis: server main `064e0fd` plus frontend landing `95ee4f4`.

## Hosting verdict

Use a **container host** (Fly/Render/etc.) for the FastAPI server at
`api.<domain>` and Vercel for the Next frontend.

Why not Vercel Python serverless for the server:

- The app is an ASGI/FastAPI relying party with startup lifespan work: pgdbm
  connects to Postgres and applies pending migrations on startup.
- It keeps operational in-memory state such as the AWID team cache; serverless
  cold starts would discard this and increase registry pressure.
- `awid-service` and `pgdbm` are local editable path dependencies in this repo
  layout; packaging them for Vercel serverless is extra risk today.
- Cert-auth endpoints are agent APIs, not static/render routes; a long-lived
  container gives simpler logs, connection management, health checks, and
  deploy rollback.

Vercel should host only the frontend renderer. The frontend needs `SERVER_ORIGIN`
pointing at the public server origin for read-only token fetches.

## Server container image

Dockerfile: `server/Dockerfile`.

Build from the repository root (not from `server/`) so the Dockerfile can copy
`server/` into the image:

```bash
docker build -f server/Dockerfile -t genui-server:064e0fd .
```

Run locally/container-host style:

```bash
docker run --rm -p 8200:8200 \
  -e GENUI_SERVER_DATABASE_URL="$NEON_DATABASE_URL" \
  -e GENUI_SERVER_AWID_REGISTRY_URL=https://api.awid.ai \
  -e GENUI_SERVER_PUBLIC_ORIGIN=https://api.<domain> \
  -e GENUI_SERVER_PRESENTATION_ORIGIN=https://<frontend-domain> \
  -e GENUI_SERVER_DB_POOL_MIN_CONNECTIONS=1 \
  -e GENUI_SERVER_DB_POOL_MAX_CONNECTIONS=5 \
  -e GENUI_SERVER_DB_STATEMENT_CACHE_SIZE=0 \
  -e LINKUP_API_KEY="$LINKUP_API_KEY" \
  genui-server:064e0fd
```

Startup behavior: `uvicorn atext.api:app` runs the FastAPI lifespan; the lifespan
constructs `GenUIDatabase` and pgdbm applies pending migrations before the app
reports startup complete. There is no separate migrate command in 064e0fd.

Container smoke performed locally:

```bash
docker build -f server/Dockerfile -t genui-server-rescoped:test .
docker run -d --rm -p 18200:8200 \
  -e GENUI_SERVER_DATABASE_URL=postgresql://juanre@host.docker.internal:5432/<fresh-db> \
  -e GENUI_SERVER_AWID_REGISTRY_URL=https://api.awid.ai \
  -e GENUI_SERVER_PUBLIC_ORIGIN=http://127.0.0.1:18200 \
  -e GENUI_SERVER_PRESENTATION_ORIGIN=http://127.0.0.1:3000 \
  -e LINKUP_API_KEY=container-smoke-placeholder \
  genui-server-rescoped:test
curl -fsS http://127.0.0.1:18200/health
```

Result: health returned `{"status":"ok","service":"genui-server"}` and the
fresh DB contained `teams`, `artifacts`, `presentation_links`, and
`schema_migrations`, proving startup migrations ran from inside the container.
No Neon secret was available in this worktree, so Operations should repeat the
same smoke against a throwaway Neon branch before promoting.

### Path-dependency gotchas

`server/pyproject.toml` is convenient for local development but contains editable
path deps:

```toml
awid-service = { path = "../../aweb/awid", editable = true }
pgdbm = { path = "../../pgdbm", editable = true }
```

Those sibling directories are **not** present in a clean container-host build
context. The Dockerfile therefore does not run a normal dependency-resolving
`pip install .`/`uv sync` against those path deps. Instead it:

- installs `awid-service` from the public `aweb` git repo at pinned commit
  `d0baafa389b600c8b0a12525797d6e38726c5252`, subdirectory `awid`;
- installs `pgdbm==0.4.1` from PyPI;
- installs the local `genui-server` package with `--no-deps` after the runtime
  deps are already present.

If Operations changes either path dependency locally, update the Dockerfile pin
before building. Longer-term, publish/pin both packages as normal registry
artifacts or vendor wheels in CI to avoid git-at-build-time dependency.

## Server env vars for 064e0fd

Required for the container-hosted server:

```bash
GENUI_SERVER_DATABASE_URL=postgresql://...        # Neon/Postgres connection
GENUI_SERVER_AWID_REGISTRY_URL=https://api.awid.ai
GENUI_SERVER_PUBLIC_ORIGIN=https://api.<domain>   # aud agents sign in aw id request --team-auth
GENUI_SERVER_PRESENTATION_ORIGIN=https://<frontend-domain>
GENUI_SERVER_DB_POOL_MIN_CONNECTIONS=1            # default; keep small for Neon pooled endpoint
GENUI_SERVER_DB_POOL_MAX_CONNECTIONS=5            # default; lower/raise only with Neon tier awareness
GENUI_SERVER_DB_STATEMENT_CACHE_SIZE=0            # default; PgBouncer/Neon pooler friendly
LINKUP_API_KEY=...                                # server-side only; enables POST /v1/search
```

Optional defaults:

```bash
GENUI_SERVER_DEFAULT_PRESENT_TTL_SECONDS=86400
GENUI_SERVER_MAX_PRESENT_TTL_SECONDS=604800
GENUI_SERVER_AUTH_CACHE_TTL_SECONDS=600
GENUI_SERVER_TIMESTAMP_SKEW_SECONDS=300
GENUI_SERVER_DB_POOL_MIN_CONNECTIONS=1
GENUI_SERVER_DB_POOL_MAX_CONNECTIONS=5
GENUI_SERVER_DB_STATEMENT_CACHE_SIZE=0
```

Database pool defaults for Render + Neon pooled endpoint:

- The server default is deliberately modest: min `1`, max `5` connections per
  Render instance.
- `GENUI_SERVER_DB_POOL_MAX_CONNECTIONS` is the primary cap Operations should
  tune down/up based on the Neon tier and Render instance count.
- `GENUI_SERVER_DB_STATEMENT_CACHE_SIZE=0` is the default because Neon pooled
  endpoints sit behind PgBouncer; disabling asyncpg's prepared-statement cache
  avoids pooler incompatibilities.

Read-only `/present/{token}` path requirements:

- Backend public `GET /present/{token}` only needs the database to resolve a
  token to one artifact version. It does not call AWID or LinkUp on that request.
- The FastAPI app still starts with the full settings above because the same
  process also serves cert-auth write/search endpoints.
- Frontend `/present/[token]` needs `SERVER_ORIGIN=https://api.<domain>` so it
  can fetch the backend public token response.
- `GENUI_SERVER_PRESENTATION_ORIGIN` is used when an agent mints a link via
  `POST /v1/present`; it is not used when rendering an already-minted token.
- `GENUI_SERVER_PUBLIC_ORIGIN` is the signed audience for team-auth requests;
  keep it as the server/API origin, not the frontend URL.

## Migrations expected by 064e0fd

The server applies pgdbm migrations automatically in `GenUIDatabase.connect()`:

- migrations directory: `server/src/atext/migrations`
- module name: `genui_server`
- current migration: `001_initial.sql`

`001_initial.sql` creates:

- `teams`
- `agents`
- `documents`
- `document_versions`
- `artifacts`
- `artifact_versions`
- `presentation_links`
- indexes for team/list lookups, version lookups, and presentation expiry
- pgdbm's `schema_migrations` row/table for module `genui_server`

Operational recommendation for Neon: run the server once against a throwaway
branch/database (or run the same pgdbm migration manager in a one-shot job), then
verify tables exist before promoting the connection string.

## Known-good seed presentation

Fresh dry-run token:

```text
GXJO0y5h91Gc9cZ2yIUeDLENdQJoJUGygiUTFote51g
```

Files:

- `docs/deploy/rescoped-demo-envelope.json` — the fresh `a2ui_operations` payload
  from the direct agent-composed run.
- `docs/deploy/rescoped-demo-seed.sql` — inserts the minimal rows needed for
  public `/present/<token>` on a throwaway hosted DB after `001_initial.sql`.

After seeding, open:

```text
https://<frontend-domain>/present/GXJO0y5h91Gc9cZ2yIUeDLENdQJoJUGygiUTFote51g
```

The backend public response should contain only:

```json
{ "a2ui": { "a2ui_operations": ["..."] }, "expires_at": "..." }
```

No team id, artifact id, creator DID, or cert fields should be returned by the
public token read.
