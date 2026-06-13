# GenUI rescope runbook

The human web UI is deliberately tiny:

- `/` explains the agent-first flow in the atext visual language.
- `/present/<token>` renders one A2UI-formatted document/artifact without login.

There is no web chat, no canvas, no `/fixed`, no `/dynamic`, and no `/catalog` route.
Agents interact through `aw id request --team-auth`.

## Flow for recording

1. Agent A creates a team document:

```bash
export GENUI_ORIGIN=http://127.0.0.1:8200
aw id request POST "$GENUI_ORIGIN/v1/documents" --team-auth --raw \
  --body '{"slug":"agentic-research-memo","title":"Agentic UI research memo","body":"Agent A draft: live web research plus declarative A2UI should produce cited, shareable surfaces."}'
```

2. Agent B appends a new version:

```bash
aw id request POST "$GENUI_ORIGIN/v1/documents/agentic-research-memo/versions" --team-auth --raw \
  --body 'Agent B revision: add source-backed validation and mint a no-login /present link for the human.'
```

3. Show attribution:

```bash
aw id request GET "$GENUI_ORIGIN/v1/documents/agentic-research-memo/versions" --team-auth --raw \
  | jq '[.[] | {version_number, created_by_alias, created_by_address, certificate_id}]'
```

4. An agent composes/stores an A2UI document artifact. The body below is short for recording; real agents can generate richer Markdown/cards/source lists.

```bash
aw id request POST "$GENUI_ORIGIN/v1/artifacts" --team-auth --raw \
  --body '{"slug":"agentic-research-surface","a2ui":{"a2ui_operations":[{"version":"v0.9","createSurface":{"surfaceId":"doc","catalogId":"https://cpk-a2ui.local/catalogs/copilotkit/v1"}},{"version":"v0.9","updateComponents":{"surfaceId":"doc","components":[{"id":"root","component":"Stack","children":["card","sources"],"gap":"lg"},{"id":"card","component":"Card","tone":"lilac","child":"brief"},{"id":"brief","component":"Markdown","text":"# Agentic UI research memo\n\n**Agent A** drafted the memo. **Agent B** appended the validation request. This is renderer-safe A2UI, not model-written HTML."},{"id":"sources","component":"Card","child":"sourceText"},{"id":"sourceText","component":"Markdown","text":"## Sources\n\n1. [LinkUp](https://www.linkup.so/) — live web search for AI agents.\n2. [A2UI](https://a2ui.org/) — declarative UI surfaces across trust boundaries."}]}},{"version":"v0.9","updateDataModel":{"surfaceId":"doc","path":"/","value":{"slug":"agentic-research-memo"}}}]}}'
```

5. Mint the present link using the `artifact_id` from step 4:

```bash
aw id request POST "$GENUI_ORIGIN/v1/present" --team-auth --raw \
  --body '{"artifact_id":"<artifact_id>","version":1}'
```

6. Open the returned URL in a fresh browser/incognito window. The human sees a document-shaped A2UI presentation, no login.

7. Open a bogus token, e.g. `/present/not-a-real-token`; it should return the friendly 404.

## Local checks

```bash
pnpm typecheck
pnpm build
pnpm smoke
```

Expected Next routes after the rescope:

```text
/                  static landing
/present/[token]   dynamic public presentation
```
