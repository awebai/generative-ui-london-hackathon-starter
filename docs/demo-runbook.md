# GenUI re-scoped video demo runbook

This is the post-rescope flow. **Do not start or record the old `:8123` concierge.**
There is no LangGraph sidecar in the demo path: team agents call the cert-auth
server directly, compose A2UI themselves, store it, mint `/present`, and hand the
human only the presentation link.

Validated dry-run: `/tmp/genui-rescoped-demo.de875a` against local AWID on
`:18010`, server on `:8200`, frontend on `:3000`.

## Processes

- FastAPI server: `server/`, public API/audience origin `http://127.0.0.1:8200`
- Next frontend: `/present/<token>` renderer at `http://127.0.0.1:3000`
- Agents: terminal workspaces with AWID team certs; no agent daemon/process

Stop stale processes before recording:

```bash
for PORT in 8123 8200 3000; do
  lsof -tiTCP:$PORT -sTCP:LISTEN | xargs -r kill
 done
```

## Start server and frontend

For a real recording, use real AWID (`GENUI_SERVER_AWID_REGISTRY_URL` unset or
`https://api.awid.ai`) and real team-member workspaces. The dry-run below used a
local registry only to prove the flow.

```bash
cd /Users/juanre/prj/awebai/genui
set -a; . ./.env; set +a  # loads LINKUP_API_KEY; do not expose it to browser/client code

# server
(
  cd server
  GENUI_SERVER_DATABASE_URL=postgresql://localhost/genui \
  GENUI_SERVER_PUBLIC_ORIGIN=http://127.0.0.1:8200 \
  GENUI_SERVER_PRESENTATION_ORIGIN=http://127.0.0.1:3000 \
  LINKUP_API_KEY="$LINKUP_API_KEY" \
  uv run uvicorn atext.api:app --host 127.0.0.1 --port 8200
)

# frontend, separate terminal
SERVER_ORIGIN=http://127.0.0.1:8200 pnpm dev:ui --hostname 127.0.0.1 --port 3000
```

## Beat 1 — two agents co-author one team document

Terminal A, from agent-a's AWID workspace:

```bash
aw id request POST http://127.0.0.1:8200/v1/documents --team-auth --raw \
  --body '{"slug":"agentic-research-memo","title":"Agentic UI research memo","body":"Agent A draft: GenUI lets AWID-authenticated team agents turn shared work into declarative A2UI surfaces and mint a no-login presentation link for the human."}' \
  | tee evidence/01-agent-a-create.json
```

Terminal B, from agent-b's AWID workspace:

```bash
aw id request POST http://127.0.0.1:8200/v1/documents/agentic-research-memo/versions --team-auth --raw \
  --body 'Agent B revision: Validate the memo with live LinkUp web search. The agent will compose renderer-safe A2UI itself, store it as an artifact, and present only the /present link to the human.' \
  | tee evidence/02-agent-b-append.json
```

Optional attribution proof:

```bash
aw id request GET http://127.0.0.1:8200/v1/documents/agentic-research-memo/versions --team-auth --raw \
  | tee evidence/03-versions.json \
  | jq '[.[] | {version_number,created_by_alias,certificate_id}]'
```

## Beat 2 — an agent searches via `/v1/search`

From either team-agent workspace:

```bash
aw id request POST http://127.0.0.1:8200/v1/search --team-auth --raw \
  --body '{"query":"LinkUp web search API for AI agents and CopilotKit A2UI declarative UI rendering","depth":"standard","max_results":5}' \
  | tee evidence/04-linkup-search.json
```

The LinkUp API key is only on the server. The response is a sourced-answer JSON
payload (`result.answer`, `result.sources`) for the agent to cite in its own A2UI.

## Beat 3 — agent composes a valid A2UI surface

Agents should use this minimal renderer-safe template and fill the Markdown text
from the document + `/v1/search` response. The critical shape is
`{ "a2ui": { "a2ui_operations": [...] } }` when storing the artifact.

```json
{
  "a2ui_operations": [
    {
      "version": "v0.9",
      "createSurface": {
        "surfaceId": "doc",
        "catalogId": "https://cpk-a2ui.local/catalogs/copilotkit/v1"
      }
    },
    {
      "version": "v0.9",
      "updateComponents": {
        "surfaceId": "doc",
        "components": [
          { "id": "root", "component": "Stack", "children": ["hero", "proof", "research"], "gap": "lg" },
          { "id": "hero", "component": "Card", "tone": "lilac", "child": "heroStack" },
          { "id": "heroStack", "component": "Stack", "children": ["overline", "title", "summary", "badges"], "gap": "sm" },
          { "id": "overline", "component": "Overline", "text": "GENUI · AWID TEAM-CERT DEMO" },
          { "id": "title", "component": "Heading", "text": "Agent-composed A2UI presentation", "level": "1" },
          { "id": "summary", "component": "Text", "text": "No concierge sidecar rendered this. A team agent used cert-auth APIs, composed renderer-safe A2UI, stored it, and minted this /present link.", "size": "lg" },
          { "id": "badges", "component": "Row", "children": ["badgeDoc", "badgeSearch", "badgePresent"], "gap": "sm" },
          { "id": "badgeDoc", "component": "Badge", "label": "team-scoped doc", "tone": "positive" },
          { "id": "badgeSearch", "component": "Badge", "label": "live LinkUp search", "tone": "info" },
          { "id": "badgePresent", "component": "Badge", "label": "no-login /present", "tone": "neutral" },
          { "id": "proof", "component": "Card", "child": "memo" },
          { "id": "memo", "component": "Markdown", "text": "# Agentic UI research memo\n\nTeam document attribution goes here." },
          { "id": "research", "component": "Card", "tone": "mint", "child": "researchMarkdown" },
          { "id": "researchMarkdown", "component": "Markdown", "text": "## Live LinkUp research\n\nSourced answer and source list go here." }
        ]
      }
    },
    {
      "version": "v0.9",
      "updateDataModel": {
        "surfaceId": "doc",
        "path": "/",
        "value": { "slug": "agentic-research-memo", "composer": "agent-a" }
      }
    }
  ]
}
```

Fresh validated envelope from the dry-run:
`docs/deploy/rescoped-demo-envelope.json`.

## Beat 4 — store the artifact and mint `/present`

```bash
aw id request POST http://127.0.0.1:8200/v1/artifacts --team-auth --raw \
  --body-file evidence/05-artifact-body.json \
  | tee evidence/06-artifact-create.json

ARTIFACT_ID=$(jq -r '.artifact_id' evidence/06-artifact-create.json)
aw id request POST http://127.0.0.1:8200/v1/present --team-auth --raw \
  --body "{\"artifact_id\":\"$ARTIFACT_ID\",\"ttl_seconds\":604800}" \
  | tee evidence/07-present-link.json
```

Dry-run token:

```text
GXJO0y5h91Gc9cZ2yIUeDLENdQJoJUGygiUTFote51g
```

Open the returned frontend URL:

```text
http://127.0.0.1:3000/present/GXJO0y5h91Gc9cZ2yIUeDLENdQJoJUGygiUTFote51g
```

## Beat 5 — prove public present is narrow

```bash
TOKEN=$(jq -r '.token' evidence/07-present-link.json)
curl -fsS "http://127.0.0.1:8200/present/$TOKEN" \
  | tee evidence/08-public-present.json \
  | jq '{keys:keys, expires_at, op_count:(.a2ui.a2ui_operations|length)}'

curl -i http://127.0.0.1:3000/present/bogus-token-for-rescoped-demo
```

Expected public server response keys are only `a2ui` and `expires_at`; bogus token
returns 404.

## Dry-run result

- Server `/v1/search`: HTTP 200 with LinkUp sourced answer and 5 sources.
- Stored artifact: `1b36e94c-88fd-4628-bf82-6a979bc94249`, version 1.
- Public server `/present/<token>`: HTTP 200, 3 A2UI operations, no team fields.
- Frontend `/present/<token>` rendered markers: `Agent-composed A2UI presentation`,
  `Live LinkUp research`, `team-scoped doc`, `no-login /present`.
- Frontend bogus token returned 404.
