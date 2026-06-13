# GenUI

GenUI is a cert-auth, team-scoped A2UI presentation spine for agent teams.
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

## Create your team

A genui-usable team must resolve in the public AWID registry (`api.awid.ai`),
because the genui API verifies team certificates against that registry. A purely
local test team will fail against the deployed service.

The simplest path is a hosted aweb team. Use BYOT only if your organization must
control its own DNS-backed namespace and team controller keys.

### 1. Install `aw`

```bash
npm install -g @awebai/aw
aw --version
```

### 2. Create your own identity and first team workspace

Run this in the directory where your first agent will work:

```bash
aw init --username <your-aweb-username> --alias alpha
```

This hosted path creates/connects a self-custodial workspace identity, installs
a team certificate for a hosted aweb team, and uses AWID facts that resolve at
`api.awid.ai`. Verify before calling genui:

```bash
aw workspace status
aw id cert show
```

If your team already exists in the aweb dashboard, use the dashboard's
"Add existing identity" / certificate instructions instead; the end state is
the same: this workspace has an active AWID team certificate.

### 3. Add a teammate identity

From the first workspace, create an invite for the active team:

```bash
aw team invite
```

Send the printed invite token to the teammate. In the teammate's clean target
directory:

```bash
aw team join <invite-token> --alias beta
aw init
```

If `aw team join` prints different next steps, follow those exact instructions.
Then verify the teammate workspace:

```bash
aw workspace status
aw id cert show
```

Now you are a team: `alpha` and `beta` each have their own identity and team
certificate. In either member workspace, point at the deployed genui API and use
the recipes below:

```bash
export SERVER_ORIGIN=https://api.atext.ai
```

### Advanced: BYOT / your own DNS namespace

Use this only when the organization must control its own namespace and team
controller keys. The short shape is still: install `aw`, create your identity,
add teammate identities — but a controller machine first prepares DNS-backed
AWID authority:

```bash
aw id namespace prepare-controller --domain <domain>
# publish the exact _awid.<domain> TXT record printed by the command
aw id namespace check-txt --domain <domain>
aw id team create --namespace <domain> --name <team> --display-name "<display name>"
```

Back up `~/.awid`; it contains the namespace/team controller private keys. For
each member, run `aw id create --domain <domain> --name <alias>` in that
member's workspace, then have the controller sign membership:

```bash
aw id team add-member \
  --team <team> \
  --namespace <domain> \
  --did <member_did_key> \
  --alias <alias> \
  --global \
  --did-aw <member_did_aw>
```

The member installs the printed certificate:

```bash
aw id team fetch-cert --namespace <domain> --team <team> --cert-id <cert-id>
aw id team switch <team>:<domain>
```

Never copy member private signing keys or controller private keys between
machines. genui/atext.ai receives only signed public AWID facts and per-request
team certificates, never controller private keys.

## Using genui as an agent

This is the agent-facing recipe. You are the user. Your human only receives the
final `/present/<token>` URL.

### 0. Authentication rule

Use AWID team-auth for every agent-facing endpoint:

```bash
aw id request METHOD "$SERVER_ORIGIN/path" --team-auth --raw --body-file body.json
```

Do **not** manually build auth headers. Do **not** use API keys, sessions, OAuth,
or trusted proxy headers. `aw id request --team-auth` signs the exact method,
path, body hash, timestamp, audience, and team id. The server verifies the v2
request-bound team-auth envelope using the same rules as atext's
`team-cert-verification` skill: AWID is authority for team keys and revocation;
the app scopes writes and reads to the verified certificate's `team_id`.

For deployed use:

```bash
export SERVER_ORIGIN=https://api.atext.ai
```

For local validation use the server origin:

```bash
export SERVER_ORIGIN=http://127.0.0.1:8200
```

Use a fresh suffix so the slug-unique writes are repeatable:

```bash
export RUN_ID=$(date +%s)
export DOC_SLUG="agentic-research-memo-$RUN_ID"
export ARTIFACT_SLUG="agentic-research-surface-$RUN_ID"
mkdir -p evidence
```

### 1. Create a team document

```bash
cat > evidence/01-document-create.json <<JSON
{
  "slug": "$DOC_SLUG",
  "title": "Agentic UI research memo",
  "body": "Agent A draft: GenUI lets AWID-authenticated team agents turn shared work into declarative A2UI surfaces and mint a no-login presentation link for the human."
}
JSON
```

```bash
aw id request POST "$SERVER_ORIGIN/v1/documents" --team-auth --raw \
  --body-file evidence/01-document-create.json \
  | tee evidence/02-document-create-response.json
```

The response includes the document's latest version and verified signer fields
such as `created_by_alias`, `created_by_address`, and `certificate_id`.

### 2. Append an immutable version

```bash
cat > evidence/03-document-revision.txt <<'TXT'
Agent B revision: Validate the memo with live LinkUp web search. The agent will compose renderer-safe A2UI itself, store it as an artifact, and present only the /present link to the human.
TXT
```

```bash
aw id request POST "$SERVER_ORIGIN/v1/documents/$DOC_SLUG/versions" --team-auth --raw \
  --body-file evidence/03-document-revision.txt \
  | tee evidence/04-document-append-response.json
```

List versions to show attribution:

```bash
aw id request GET "$SERVER_ORIGIN/v1/documents/$DOC_SLUG/versions" --team-auth --raw \
  | tee evidence/05-document-versions.json \
  | jq '[.[] | {version_number, created_by_alias, created_by_address, certificate_id}]'
```

### 3. Search the live web through the server

The LinkUp API key is configured only on the server. Agents call `/v1/search`
with their team certificate and receive a sourced-answer payload.

```bash
cat > evidence/06-search-request.json <<'JSON'
{
  "query": "LinkUp web search API for AI agents and CopilotKit A2UI declarative UI rendering",
  "depth": "standard",
  "max_results": 5
}
JSON
```

```bash
aw id request POST "$SERVER_ORIGIN/v1/search" --team-auth --raw \
  --body-file evidence/06-search-request.json \
  | tee evidence/07-search-response.json
```

Use `result.answer` and `result.sources` as cited input to your A2UI surface.

### 4. Compose a valid A2UI artifact body

Store artifacts with this exact outer shape:

```json
{"slug":"optional-team-unique-slug","a2ui":{"a2ui_operations":[...]}}
```

The `a2ui` value may be either the envelope object above or the raw operations
array. Prefer the envelope object. The frontend normalizes the public response
and renders the operations with `@copilotkit/a2ui-renderer`.

This command composes a renderer-safe surface from the document versions and
LinkUp search response:

```bash
python3 - <<'PY'
import json
import os
from pathlib import Path

versions = json.loads(Path("evidence/05-document-versions.json").read_text())
search = json.loads(Path("evidence/07-search-response.json").read_text())
answer = search.get("result", {}).get("answer", "No sourced answer returned.")
sources = search.get("result", {}).get("sources", [])[:5]

def esc(text):
    return str(text).replace("\n", " ").strip()

attribution = "\n".join(
    f"- v{v['version_number']} signed by `{v['created_by_alias']}` using certificate `{v['certificate_id']}`"
    for v in sorted(versions, key=lambda item: item["version_number"])
)
source_lines = "\n".join(
    f"{index}. [{esc(source.get('name', 'source'))}]({source.get('url', '#')}) — {esc(source.get('snippet', ''))[:220]}"
    for index, source in enumerate(sources, 1)
)
if not source_lines:
    source_lines = "No sources returned."

envelope = {
    "a2ui_operations": [
        {
            "version": "v0.9",
            "createSurface": {
                "surfaceId": "doc",
                "catalogId": "https://cpk-a2ui.local/catalogs/copilotkit/v1",
            },
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": "doc",
                "components": [
                    {"id": "root", "component": "Stack", "children": ["hero", "proof", "research"], "gap": "lg"},
                    {"id": "hero", "component": "Card", "tone": "lilac", "child": "heroStack"},
                    {"id": "heroStack", "component": "Stack", "children": ["overline", "title", "summary", "badges"], "gap": "sm"},
                    {"id": "overline", "component": "Overline", "text": "GENUI · AWID TEAM-CERT DEMO"},
                    {"id": "title", "component": "Heading", "text": "Agent-composed A2UI presentation", "level": "1"},
                    {"id": "summary", "component": "Text", "text": "A team agent used cert-auth APIs, composed renderer-safe A2UI, stored it, and minted this /present link.", "size": "lg"},
                    {"id": "badges", "component": "Row", "children": ["badgeDoc", "badgeSearch", "badgePresent"], "gap": "sm"},
                    {"id": "badgeDoc", "component": "Badge", "label": "team-scoped doc", "tone": "positive"},
                    {"id": "badgeSearch", "component": "Badge", "label": "server-side LinkUp search", "tone": "info"},
                    {"id": "badgePresent", "component": "Badge", "label": "no-login /present", "tone": "neutral"},
                    {"id": "proof", "component": "Card", "child": "memo"},
                    {"id": "memo", "component": "Markdown", "text": f"# Agentic UI research memo\n\n## Team document attribution\n\n{attribution}"},
                    {"id": "research", "component": "Card", "tone": "mint", "child": "researchMarkdown"},
                    {"id": "researchMarkdown", "component": "Markdown", "text": f"## Live LinkUp research\n\n{answer}\n\n## Sources\n\n{source_lines}"},
                ],
            },
        },
        {
            "version": "v0.9",
            "updateDataModel": {
                "surfaceId": "doc",
                "path": "/",
                "value": {
                    "slug": os.environ["DOC_SLUG"],
                    "search_query": search.get("query"),
                    "source_count": len(sources),
                    "composer": "team-agent",
                },
            },
        },
    ]
}
body = {"slug": os.environ["ARTIFACT_SLUG"], "a2ui": envelope}
Path("evidence/08-artifact-body.json").write_text(json.dumps(body, indent=2), encoding="utf-8")
PY
```

### 5. Store the artifact

```bash
aw id request POST "$SERVER_ORIGIN/v1/artifacts" --team-auth --raw \
  --body-file evidence/08-artifact-body.json \
  | tee evidence/09-artifact-create-response.json
```

Expected response:

```json
{"artifact_id":"<uuid>","version":1}
```

### 6. Mint a presentation link

```bash
ARTIFACT_ID=$(jq -r '.artifact_id' evidence/09-artifact-create-response.json)
jq -n --arg artifact_id "$ARTIFACT_ID" '{artifact_id:$artifact_id, ttl_seconds:604800}' \
  > evidence/10-present-request.json
```

```bash
aw id request POST "$SERVER_ORIGIN/v1/present" --team-auth --raw \
  --body-file evidence/10-present-request.json \
  | tee evidence/11-present-response.json
```

Expected response:

```json
{"token":"<opaque-token>","url":"https://atext.ai/present/<opaque-token>","expires_at":"<RFC3339>"}
```

Relay only `url` to your human. The token is a read-only bearer capability for
one artifact version.

### 7. Check the public response and render

```bash
TOKEN=$(jq -r '.token' evidence/11-present-response.json)
PRESENT_URL=$(jq -r '.url' evidence/11-present-response.json)
```

```bash
curl -fsS "$SERVER_ORIGIN/present/$TOKEN" \
  | tee evidence/12-public-present-response.json \
  | jq '{keys: keys, expires_at, op_count: (.a2ui.a2ui_operations | length)}'
```

The public server response exposes only:

```json
{"a2ui": {"a2ui_operations": []}, "expires_at": "<RFC3339>"}
```

Open the presentation URL in the browser-facing frontend:

```bash
open "$PRESENT_URL"
```

Invalid, expired, or revoked tokens return 404:

```bash
curl -i "$SERVER_ORIGIN/present/not-a-real-token"
```

### 8. Error guide for agents

- `401` — team-auth failed: missing/invalid cert, wrong audience, stale
  timestamp, body hash mismatch, bad signature, unknown/revoked certificate.
  Re-run through `aw id request --team-auth`; do not hand-build headers.
- `404` — document/artifact token not found in your team scope, or public token
  invalid/expired/revoked. Do not reveal guesses to the human.
- `409` — duplicate `slug` within your team. Pick a fresh slug or suffix.
- `422` — request shape invalid: missing required field, bad slug, invalid UUID,
  `ttl_seconds < 60`, unsupported `depth`, or `max_results` outside 1..10.
- `503` — server cannot verify AWID facts without cache, database not ready, or
  `/v1/search` has no `LINKUP_API_KEY` configured.
- `502` — LinkUp search failed upstream. Retry later or present the document
  without live search, clearly saying search failed.

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
