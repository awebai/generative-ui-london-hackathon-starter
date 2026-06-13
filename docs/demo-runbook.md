# GenUI demo runbook — direct team-agent flow

GenUI no longer runs a concierge/LangGraph sidecar. The human drives their own
team agents (Claude Code, Pi, etc.). Those agents use real AWID team-auth calls
to the server:

1. co-author text documents;
2. search the live web through `POST /v1/search` (server-side LinkUp key);
3. compose an A2UI view of the document/research;
4. `POST /v1/artifacts` + `POST /v1/present` to mint a no-login URL;
5. the human opens `/present/<token>` in the Next frontend.

## Stack

```bash
# server: keep the AWID registry default for real teams unless explicitly testing locally
cd /Users/juanre/prj/awebai/genui/server
GENUI_SERVER_DATABASE_URL=postgresql://localhost/genui \
GENUI_SERVER_PUBLIC_ORIGIN=http://127.0.0.1:8200 \
GENUI_SERVER_PRESENTATION_ORIGIN=http://127.0.0.1:3000 \
LINKUP_API_KEY=<real key> \
uv run uvicorn atext.api:app --host 127.0.0.1 --port 8200

# frontend renderer
cd /Users/juanre/prj/awebai/genui
SERVER_ORIGIN=http://127.0.0.1:8200 pnpm dev:ui --hostname 127.0.0.1 --port 3000
```

No `agent/` process is required.

## Team-agent commands

Run from a workspace with a real AWID team certificate.

Create a document:

```bash
aw id request POST http://127.0.0.1:8200/v1/documents --team-auth --raw \
  --body '{"slug":"research-brief","title":"Research brief","body":"Agent A draft."}'
```

Append a version:

```bash
aw id request POST http://127.0.0.1:8200/v1/documents/research-brief/versions --team-auth --raw \
  --body 'Agent B revision with search findings.'
```

Search live web via server-side LinkUp:

```bash
aw id request POST http://127.0.0.1:8200/v1/search --team-auth --raw \
  --body '{"query":"LinkUp web search API and CopilotKit A2UI","depth":"standard","max_results":5}'
```

Compose an A2UI doc view locally (example minimal markdown surface):

```bash
A2UI='{"a2ui_operations":[{"createSurface":{"surfaceId":"doc-view","catalogId":"https://cpk-a2ui.local/catalogs/copilotkit/v1"}},{"updateComponents":{"surfaceId":"doc-view","components":[{"id":"root","component":"Stack","children":["title","body"],"gap":"md"},{"id":"title","component":"Heading","text":"Research brief","level":"1"},{"id":"body","component":"Markdown","text":"## What changed\\n\\nAgent A and Agent B co-authored this doc. LinkUp search supplied citations; this A2UI surface is what the human sees."}]}},{"updateDataModel":{"surfaceId":"doc-view","path":"/","value":{}}}]}'
```

Store artifact and mint present link:

```bash
ARTIFACT=$(aw id request POST http://127.0.0.1:8200/v1/artifacts --team-auth --raw \
  --body "{\"a2ui\":$A2UI,\"slug\":\"research-brief-view\"}")
ARTIFACT_ID=$(python3 -c 'import json,sys; print(json.load(sys.stdin)["artifact_id"])' <<<"$ARTIFACT")
aw id request POST http://127.0.0.1:8200/v1/present --team-auth --raw \
  --body "{\"artifact_id\":\"$ARTIFACT_ID\"}"
```

Open the returned `url` in a browser. Open a bogus token to show the 404:

```text
http://127.0.0.1:3000/present/bogus-token-for-demo
```
