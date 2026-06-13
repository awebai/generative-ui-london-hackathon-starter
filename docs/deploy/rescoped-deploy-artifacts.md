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

## Server env vars for 064e0fd

Required for the container-hosted server:

```bash
GENUI_SERVER_DATABASE_URL=postgresql://...        # Neon/Postgres connection
GENUI_SERVER_AWID_REGISTRY_URL=https://api.awid.ai
GENUI_SERVER_PUBLIC_ORIGIN=https://api.<domain>   # aud agents sign in aw id request --team-auth
GENUI_SERVER_PRESENTATION_ORIGIN=https://<frontend-domain>
LINKUP_API_KEY=...                                # server-side only; enables POST /v1/search
```

Optional defaults:

```bash
GENUI_SERVER_DEFAULT_PRESENT_TTL_SECONDS=86400
GENUI_SERVER_MAX_PRESENT_TTL_SECONDS=604800
GENUI_SERVER_AUTH_CACHE_TTL_SECONDS=600
GENUI_SERVER_TIMESTAMP_SKEW_SECONDS=300
```

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
