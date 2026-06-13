---
name: "genui:present-to-human"
description: Use when an agent needs to show a human work from genui/atext.ai: authenticate with AWID team certs, write or read team docs, optionally search with /v1/search, compose renderer-safe A2UI, store it as an artifact, mint /present, and relay only the URL. This is for USING the system, not editing the codebase.
version: 1.0.0
---

# genui:present-to-human

Use this skill when you are an agent and you need to show your human a rendered
A2UI document through genui/atext.ai.

The human does not log in and does not operate a chat/canvas UI. You do the work
with your AWID team certificate, then hand the human a single `/present/<token>`
URL.

## Rules

- Use `aw id request --team-auth --raw` for every agent-facing request.
- Do not manually construct AWID/auth headers. If you are implementing or
  reviewing auth, use atext's `team-cert-verification` skill. As a client,
  shell to `aw id request --team-auth`.
- Do not send `team_id` in bodies and expect it to matter. The server scopes by
  the verified certificate's `team_id`.
- Keep `LINKUP_API_KEY` server-side. Agents call `POST /v1/search`; clients do
  not call LinkUp directly in this workflow.
- Relay only the final `url` from `POST /v1/present` to the human.
- Treat the token as bearer access to one read-only artifact version.

## Prerequisite: be in an AWID team

Before using genui, this workspace must hold an AWID team certificate that
resolves in the public AWID registry (`api.awid.ai`). Check:

```bash
aw workspace status
aw id cert show
```

If the team does not exist yet, follow the README `/llms.txt` "Create your
team" on-ramp first. The simplest hosted path is: install `aw`; run
`aw init --username <your-aweb-username> --alias alpha`; invite a teammate with
`aw team invite`; in the teammate's clean directory run
`aw team join <invite-token> --alias beta` then `aw init`. BYOT/DNS-backed teams
also work, but only after the namespace/team resolves at `api.awid.ai` and each
member has fetched and switched to its team certificate.

## Quick workflow

Set the API origin. For deployed:

```bash
export SERVER_ORIGIN=https://api.atext.ai
```

For local validation:

```bash
export SERVER_ORIGIN=http://127.0.0.1:8200
```

Make repeatable slugs:

```bash
export RUN_ID=$(date +%s)
export DOC_SLUG="agentic-research-memo-$RUN_ID"
export ARTIFACT_SLUG="agentic-research-surface-$RUN_ID"
mkdir -p evidence
```

### 1. Write the team document

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

Append a new immutable version:

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

Show attribution:

```bash
aw id request GET "$SERVER_ORIGIN/v1/documents/$DOC_SLUG/versions" --team-auth --raw \
  | tee evidence/05-document-versions.json \
  | jq '[.[] | {version_number, created_by_alias, created_by_address, certificate_id}]'
```

### 2. Search, if useful

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

If this returns 503 (`linkup_not_configured`) or 502 (`linkup_search_failed`),
you may still present the document. State clearly in the A2UI Markdown that live
search failed or was not configured.

### 3. Compose the A2UI artifact body

Use `genui:compose-a2ui` for the envelope rules. The artifact request must be:

```json
{"slug":"team-unique-slug","a2ui":{"a2ui_operations":[...]}}
```

If you followed the README/llms recipe, compose:

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
) or "No sources returned."

envelope = {
    "a2ui_operations": [
        {"version":"v0.9","createSurface":{"surfaceId":"doc","catalogId":"https://cpk-a2ui.local/catalogs/copilotkit/v1"}},
        {"version":"v0.9","updateComponents":{"surfaceId":"doc","components":[
            {"id":"root","component":"Stack","children":["hero","proof","research"],"gap":"lg"},
            {"id":"hero","component":"Card","tone":"lilac","child":"heroStack"},
            {"id":"heroStack","component":"Stack","children":["overline","title","summary","badges"],"gap":"sm"},
            {"id":"overline","component":"Overline","text":"GENUI · AWID TEAM-CERT DEMO"},
            {"id":"title","component":"Heading","text":"Agent-composed A2UI presentation","level":"1"},
            {"id":"summary","component":"Text","text":"A team agent used cert-auth APIs, composed renderer-safe A2UI, stored it, and minted this /present link.","size":"lg"},
            {"id":"badges","component":"Row","children":["badgeDoc","badgeSearch","badgePresent"],"gap":"sm"},
            {"id":"badgeDoc","component":"Badge","label":"team-scoped doc","tone":"positive"},
            {"id":"badgeSearch","component":"Badge","label":"server-side LinkUp search","tone":"info"},
            {"id":"badgePresent","component":"Badge","label":"no-login /present","tone":"neutral"},
            {"id":"proof","component":"Card","child":"memo"},
            {"id":"memo","component":"Markdown","text":f"# Agentic UI research memo\n\n## Team document attribution\n\n{attribution}"},
            {"id":"research","component":"Card","tone":"mint","child":"researchMarkdown"},
            {"id":"researchMarkdown","component":"Markdown","text":f"## Live LinkUp research\n\n{answer}\n\n## Sources\n\n{source_lines}"}
        ]}},
        {"version":"v0.9","updateDataModel":{"surfaceId":"doc","path":"/","value":{"slug":os.environ["DOC_SLUG"],"search_query":search.get("query"),"source_count":len(sources),"composer":"team-agent"}}},
    ]
}
body = {"slug": os.environ["ARTIFACT_SLUG"], "a2ui": envelope}
Path("evidence/08-artifact-body.json").write_text(json.dumps(body, indent=2), encoding="utf-8")
PY
```

### 4. Store the artifact

```bash
aw id request POST "$SERVER_ORIGIN/v1/artifacts" --team-auth --raw \
  --body-file evidence/08-artifact-body.json \
  | tee evidence/09-artifact-create-response.json
```

### 5. Mint the present link

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

### 6. Relay the URL

```bash
jq -r '.url' evidence/11-present-response.json
```

Send only that URL to the human. Do not ask the human to call APIs or paste
certificates. If you are local, open the returned frontend URL yourself:

```bash
PRESENT_URL=$(jq -r '.url' evidence/11-present-response.json)
open "$PRESENT_URL"
```

### 7. Verify narrow public access

```bash
TOKEN=$(jq -r '.token' evidence/11-present-response.json)
curl -fsS "$SERVER_ORIGIN/present/$TOKEN" \
  | jq '{keys: keys, expires_at, op_count: (.a2ui.a2ui_operations | length)}'
```

Expected keys: `a2ui`, `expires_at`. No `team_id`, `artifact_id`, DID, alias, or
certificate fields.

## Error handling

- 401: auth failed. Re-run with `aw id request --team-auth` from the correct
  team workspace.
- 404: the document/artifact is not in your team scope, or the public token is
  invalid/expired/revoked.
- 409: slug already exists. Change `DOC_SLUG` or `ARTIFACT_SLUG`.
- 422: invalid request body. Check slug pattern, required fields, UUIDs,
  `ttl_seconds >= 60`, search `depth`, and `max_results`.
- 503: AWID/database/search not configured or unavailable.
- 502: LinkUp failed upstream.

## Done means

- You have a stored artifact response with `artifact_id` and `version`.
- You have a present response with `token`, `url`, and `expires_at`.
- You relayed `url` to the human.
- A bogus `/present/not-a-real-token` returns 404.
