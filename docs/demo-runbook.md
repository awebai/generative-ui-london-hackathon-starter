# GenUI video demo runbook

This is the repeatable screen-recording path for the live demo. It uses real AWID/BYOT team certificates, real `aw id request --team-auth`, real LinkUp + Gemini, and `OFFLINE` must stay unset.

## Current dry-run (green)

- Repo: `/Users/juanre/prj/awebai/genui`
- Branch used for polish: `developer-2-demo-polish`
- Demo root: `/tmp/genui-video-demo.8o1OC9`
- Team: `default:genui-video-1781359819.test`
- Workspaces:
  - Agent A: `/tmp/genui-video-demo.8o1OC9/agent-a`
  - Agent B: `/tmp/genui-video-demo.8o1OC9/agent-b`
  - Concierge: `/tmp/genui-video-demo.8o1OC9/concierge`
- Frontend: `http://127.0.0.1:3000`
- Final present URL: `http://127.0.0.1:3000/present/-ichQIwhlyFeLjl8nZOhF9UcVudZfNIuKN2WjlCLZoA`
- Evidence dir: `/tmp/genui-video-demo.8o1OC9/evidence`

## One-time stack start

If AWID is not already running on `:18010`:

```bash
cd /Users/juanre/prj/awebai/aweb/awid
POSTGRES_PASSWORD=awid AWID_PORT=18010 docker compose -p genui-video-awid up -d --build
curl -fsS http://127.0.0.1:18010/health
```

Start the genui server, agent, and frontend from the genui repo:

```bash
cd /Users/juanre/prj/awebai/genui
set -a; . ./.env; set +a   # loads GEMINI_API_KEY + LINKUP_API_KEY; leave OFFLINE unset

export DEMO_ROOT=/tmp/genui-video-demo.$(openssl rand -hex 3)
export DOMAIN=genui-video-$(date +%s).test
export TEAM=default
export REG=http://127.0.0.1:18010
export DB=genui_video_$(date +%s)
mkdir -p "$DEMO_ROOT"/{controller,agent-a,agent-b,concierge,logs,evidence}
createdb "$DB"
```

## Provision one BYOT team with three members

```bash
cd "$DEMO_ROOT/controller"
aw id create --name controller --domain "$DOMAIN" --registry "$REG" --skip-dns-verify --json > "$DEMO_ROOT/controller-id.json"
aw id team create --namespace "$DOMAIN" --name "$TEAM" --display-name "genui video demo" --registry "$REG" --json > "$DEMO_ROOT/team.json"

for NAME in agent-a agent-b concierge; do
  cd "$DEMO_ROOT/$NAME"
  AWID_REGISTRY_URL="$REG" aw id create --name "$NAME" --domain "$DOMAIN" --registry "$REG" --skip-dns-verify --json > "$DEMO_ROOT/$NAME-id.json"
  DID=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["did_key"])' "$DEMO_ROOT/$NAME-id.json")
  DIDAW=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["did_aw"])' "$DEMO_ROOT/$NAME-id.json")

  cd "$DEMO_ROOT/controller"
  AWID_REGISTRY_URL="$REG" aw id team add-member --namespace "$DOMAIN" --team "$TEAM" \
    --did "$DID" --did-aw "$DIDAW" --address "$DOMAIN/$NAME" --alias "$NAME" --global --json \
    > "$DEMO_ROOT/$NAME-add.json"
  CERT=$(python3 -c 'import json,sys;print(json.load(open(sys.argv[1]))["certificate_id"])' "$DEMO_ROOT/$NAME-add.json")

  cd "$DEMO_ROOT/$NAME"
  AWID_REGISTRY_URL="$REG" aw id team fetch-cert --namespace "$DOMAIN" --team "$TEAM" --cert-id "$CERT" --json \
    > "$DEMO_ROOT/$NAME-fetch.json"

  python3 - <<PY "$NAME" "$DOMAIN" "$DEMO_ROOT/$NAME"
from pathlib import Path
from datetime import datetime, timezone
import sys, uuid
name, domain, root = sys.argv[1:]
team=f"default:{domain}"
cert=f"team-certs/default__{domain}.pem"
now=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
Path(root,'.aw','workspace.yaml').write_text(f'''aweb_url: https://app.aweb.ai/api
memberships:
    - team_id: {team}
      alias: {name}
      workspace_id: {uuid.uuid4()}
      cert_path: {cert}
      joined_at: "{now}"
human_name: juanre
agent_type: agent
canonical_origin: local/genui-video-demo
hostname: altair.local
workspace_path: {root}
updated_at: "{now}"
''')
PY
  aw id team list
 done
```

## Start services

```bash
cd /Users/juanre/prj/awebai/genui

(
  cd server
  GENUI_SERVER_DATABASE_URL="postgresql://localhost/$DB" \
  GENUI_SERVER_AWID_REGISTRY_URL="$REG" \
  GENUI_SERVER_PUBLIC_ORIGIN=http://127.0.0.1:8200 \
  GENUI_SERVER_PRESENTATION_ORIGIN=http://127.0.0.1:3000 \
  uv run uvicorn atext.api:app --host 127.0.0.1 --port 8200
) > "$DEMO_ROOT/logs/server.log" 2>&1 & echo $! > "$DEMO_ROOT/logs/server.pid"

(
  cd agent
  SERVER_ORIGIN=http://127.0.0.1:8200 \
  GENUI_AW_CWD="$DEMO_ROOT/concierge" \
  GEMINI_API_KEY="$GEMINI_API_KEY" \
  LINKUP_API_KEY="$LINKUP_API_KEY" \
  uv run uvicorn main:app --host 127.0.0.1 --port 8123
) > "$DEMO_ROOT/logs/agent.log" 2>&1 & echo $! > "$DEMO_ROOT/logs/agent.pid"

(
  SERVER_ORIGIN=http://127.0.0.1:8200 \
  FIXED_AGENT_URL=http://127.0.0.1:8123/fixed \
  DYNAMIC_AGENT_URL=http://127.0.0.1:8123/dynamic \
  LEGAL_AGENT_URL=http://127.0.0.1:8123/legal \
  pnpm exec next dev --turbopack --hostname 127.0.0.1 --port 3000
) > "$DEMO_ROOT/logs/frontend.log" 2>&1 & echo $! > "$DEMO_ROOT/logs/frontend.pid"

curl -fsS http://127.0.0.1:8200/health
curl -fsS http://127.0.0.1:8123/ >/dev/null
curl -fsS http://127.0.0.1:3000/ >/dev/null
```

## Recordable flow

### Beat 1 — Agent A + Agent B co-author one team document

Show two terminals side by side.

Terminal A:

```bash
cd "$DEMO_ROOT/agent-a"
aw id request POST http://127.0.0.1:8200/v1/documents --team-auth --raw --body '{"slug":"agentic-research-memo","title":"Agentic UI research memo","body":"Agent A draft: Our demo topic is agentic web research UI. We need to validate how live web search plus declarative A2UI can produce cited, shareable surfaces."}' \
  | tee "$DEMO_ROOT/evidence/agent-a-create.json" \
  | jq '{slug,current_version,latest:{version_number:.latest.version_number,created_by_alias:.latest.created_by_alias,created_by_address:.latest.created_by_address,certificate_id:.latest.certificate_id}}'
```

Terminal B:

```bash
cd "$DEMO_ROOT/agent-b"
aw id request POST http://127.0.0.1:8200/v1/documents/agentic-research-memo/versions --team-auth --raw \
  --body 'Agent B revision: Add emphasis that the concierge validates the topic with real LinkUp sources and then mints a no-login /present link for humans.' \
  | tee "$DEMO_ROOT/evidence/agent-b-append.json" \
  | jq '{slug,current_version,latest:{version_number:.latest.version_number,created_by_alias:.latest.created_by_alias,created_by_address:.latest.created_by_address,certificate_id:.latest.certificate_id}}'
```

Optional attribution proof:

```bash
cd "$DEMO_ROOT/agent-a"
aw id request GET http://127.0.0.1:8200/v1/documents/agentic-research-memo/versions --team-auth --raw \
  | jq '[.[] | {version_number,created_by_alias,created_by_address,certificate_id}]'
```

Narration: both agents are in one BYOT team; each version is attributed to the verified member certificate.

### Beat 2 — Ask the web chat concierge

Open `http://127.0.0.1:3000/fixed` or `http://127.0.0.1:3000/dynamic`.

Paste this prompt:

```text
Research current public sources on LinkUp's web search API for AI agents and CopilotKit A2UI/AG-UI declarative rendering. Include LinkUp-owned source pages if LinkUp returns them. Build a concise cited A2UI brief with markdown summary and sources, then present it to the human. This validates the topic of our shared memo; do not claim you read the memo.
```

Narration: the concierge researches the topic the operator relays. It does not read the memo body in v1.

### Beat 3 — Watch the canvas

The canvas should render a real A2UI surface: hero card, badges, markdown summary, and sources. This is not HTML generated by the model; it is `createSurface` + `updateComponents` + `updateDataModel` through the catalog.

### Beat 4 — Copy the /present link

The assistant should return a URL like:

```text
http://127.0.0.1:3000/present/<token>
```

Final dry-run URL:

```text
http://127.0.0.1:3000/present/-ichQIwhlyFeLjl8nZOhF9UcVudZfNIuKN2WjlCLZoA
```

Artifact attribution note: v1 artifacts are attributed to the concierge identity. `originating_agent` for Agent A/B is not wired yet.

### Beat 5 — Fresh browser + bogus token

Open the link in a fresh browser/incognito window. It should render the cited surface with no login.

Then open:

```text
http://127.0.0.1:3000/present/bogus-demo-token-final
```

It should render the friendly `Link unavailable` 404. The server also returns 404 for `http://127.0.0.1:8200/present/bogus-demo-token-final`.

## Final dry-run evidence

- Agent A create: `/tmp/genui-video-demo.8o1OC9/evidence/01-agent-a-create.json`
- Agent B append: `/tmp/genui-video-demo.8o1OC9/evidence/02-agent-b-append.json`
- Version attribution list: `/tmp/genui-video-demo.8o1OC9/evidence/03-agent-a-list-versions.json`
- Final chat stream: `/tmp/genui-video-demo.8o1OC9/evidence/27-final-linkup-stream.txt`
- Public present response: `/tmp/genui-video-demo.8o1OC9/evidence/29-public-present--ichQIwhlyFeLjl8nZOhF9UcVudZfNIuKN2WjlCLZoA.json`
- Final A2UI envelope: `/tmp/genui-video-demo.8o1OC9/evidence/30-envelope--ichQIwhlyFeLjl8nZOhF9UcVudZfNIuKN2WjlCLZoA.json`
- Rendered page HTML: `/tmp/genui-video-demo.8o1OC9/evidence/32-frontend-present-linkup.html`

Dry-run checks passed: landing 200 with product copy, `/present` 200 with `LINKUP RESEARCH`, `Live LinkUp search`, `Cited markdown`, `No-login link`, `Sources`, `linkup.so`, and `CopilotKit`; bogus server and frontend tokens returned 404.
