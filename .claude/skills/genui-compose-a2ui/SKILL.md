---
name: "genui:compose-a2ui"
description: Use when an agent must compose a valid A2UI surface for genui/atext.ai as a client: choose catalog components, emit createSurface/updateComponents/updateDataModel operations, wrap them for POST /v1/artifacts, and avoid invalid component trees. This is for USING the system, not adding new catalog components.
version: 1.0.0
---

# genui:compose-a2ui

Use this skill when you need to compose the A2UI JSON that genui stores and
renders at `/present/<token>`.

This skill is about **using** the existing catalog. It is not for adding a new
component to the codebase. To add new catalog primitives, use
`create-a2ui-widget` instead.

## Store shape

`POST /v1/artifacts` accepts exactly this client shape:

```json
{
  "slug": "optional-team-unique-slug",
  "a2ui": {
    "a2ui_operations": []
  }
}
```

`slug` is optional but useful. It must be unique within the team if provided.

The public present response later returns:

```json
{
  "a2ui": {
    "a2ui_operations": []
  },
  "expires_at": "<RFC3339>"
}
```

No team fields are exposed publicly.

## Operation rules

A renderable surface needs three operations in this order:

1. `createSurface` with a stable `surfaceId` and the live catalog id.
2. `updateComponents` with a connected component tree.
3. Optional but recommended `updateDataModel` with metadata or path-bound data.

Use this catalog id:

```text
https://cpk-a2ui.local/catalogs/copilotkit/v1
```

Use simple component IDs (`root`, `hero`, `summary`, `sources`). IDs are local to
the surface. Every child reference must point to another component in the same
`components` array.

## Safe component set

The current renderer supports these component names from the catalog:

- Layout: `Stack`, `Row`, `Grid`, `Section`, `Card`, `Divider`
- Text: `Heading`, `Text`, `Markdown`, `Overline`, `Badge`, `Callout`, `BulletList`
- Data: `StatCard`, `BarChart`, `HorizontalBarChart`, `LineChart`, `DonutChart`, `ScatterChart`, `DataTable`
- Controls: `Button`, `ChoiceChips`

For a reliable presentation document, prefer:

- `Stack` root
- `Card` sections
- `Heading` for title
- `Text` for short plain prose
- `Markdown` for cited summaries and source lists
- `Badge` in a `Row` for proof labels

Avoid inventing component names. Unknown components will not render.

## Props that most often matter

- `Stack`: `{ "children": ["childId"], "gap": "sm"|"md"|"lg"|"xl" }`
- `Row`: `{ "children": ["childId"], "gap": "sm"|"md"|"lg" }`
- `Card`: `{ "child": "childId", "tone": "default"|"lilac"|"mint"|"warning" }`
- `Heading`: `{ "text": "...", "level": "1"|"2"|"3" }`
- `Text`: `{ "text": "...", "tone": "muted", "size": "sm"|"md"|"lg" }`
- `Markdown`: `{ "text": "# Heading\n\n[link](https://example.com)" }`
- `Badge`: `{ "label": "...", "tone": "neutral"|"positive"|"warning"|"danger"|"info" }`
- `DataTable`: `{ "columns": [{"key":"name","label":"Name"}], "rows": [{"name":"A"}] }`

Some props may bind to data-model paths, e.g. `{ "text": {"path":"/summary"} }`,
but literal values are safer for first-pass surfaces.

## Worked example envelope that renders

This envelope is intentionally small but complete. It creates one surface named
`doc`, renders a title card, attribution card, and cited Markdown research card,
and writes metadata to the data model.

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
          {
            "id": "root",
            "component": "Stack",
            "children": ["hero", "proof", "research"],
            "gap": "lg"
          },
          {
            "id": "hero",
            "component": "Card",
            "tone": "lilac",
            "child": "heroStack"
          },
          {
            "id": "heroStack",
            "component": "Stack",
            "children": ["overline", "title", "summary", "badges"],
            "gap": "sm"
          },
          {
            "id": "overline",
            "component": "Overline",
            "text": "GENUI · AWID TEAM-CERT DEMO"
          },
          {
            "id": "title",
            "component": "Heading",
            "text": "Agent-composed A2UI presentation",
            "level": "1"
          },
          {
            "id": "summary",
            "component": "Text",
            "text": "A verified team agent composed this renderer-safe A2UI, stored it as an artifact, and minted a no-login /present link.",
            "size": "lg"
          },
          {
            "id": "badges",
            "component": "Row",
            "children": ["badgeDoc", "badgeSearch", "badgePresent"],
            "gap": "sm"
          },
          {
            "id": "badgeDoc",
            "component": "Badge",
            "label": "team-scoped doc",
            "tone": "positive"
          },
          {
            "id": "badgeSearch",
            "component": "Badge",
            "label": "server-side LinkUp search",
            "tone": "info"
          },
          {
            "id": "badgePresent",
            "component": "Badge",
            "label": "no-login /present",
            "tone": "neutral"
          },
          {
            "id": "proof",
            "component": "Card",
            "child": "memo"
          },
          {
            "id": "memo",
            "component": "Markdown",
            "text": "# Agentic UI research memo\n\n## Team document attribution\n\n- v1 signed by `agent-a` using certificate `<certificate_id>`\n- v2 signed by `agent-b` using certificate `<certificate_id>`"
          },
          {
            "id": "research",
            "component": "Card",
            "tone": "mint",
            "child": "researchMarkdown"
          },
          {
            "id": "researchMarkdown",
            "component": "Markdown",
            "text": "## Live LinkUp research\n\nA sourced answer goes here. Keep citations in Markdown.\n\n## Sources\n\n1. [LinkUp](https://www.linkup.so/) — Web search for AI agents.\n2. [CopilotKit A2UI](https://docs.copilotkit.ai/generative-ui/a2ui) — Declarative UI rendering."
          }
        ]
      }
    },
    {
      "version": "v0.9",
      "updateDataModel": {
        "surfaceId": "doc",
        "path": "/",
        "value": {
          "slug": "agentic-research-memo",
          "source_count": 2,
          "composer": "team-agent"
        }
      }
    }
  ]
}
```

Wrap it for storage:

```json
{
  "slug": "agentic-research-surface",
  "a2ui": {
    "a2ui_operations": [
      "...operations above..."
    ]
  }
}
```

## Store and present the example

Assuming `evidence/08-artifact-body.json` contains the storage body above and
`SERVER_ORIGIN` points at the genui API origin that matches
`GENUI_SERVER_PUBLIC_ORIGIN` (`https://api.atext.ai` deployed, or
`http://127.0.0.1:8200` locally). Open the human-facing `url` returned by
`/v1/present`; do not derive it from `SERVER_ORIGIN` unless API and frontend
share an origin:

```bash
aw id request POST "$SERVER_ORIGIN/v1/artifacts" --team-auth --raw \
  --body-file evidence/08-artifact-body.json \
  | tee evidence/09-artifact-create-response.json
```

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

Open the rendered view for the human when you have desktop access, and always
print the URL as fallback:

```bash
PRESENT_URL=$(jq -r '.url' evidence/11-present-response.json)
if command -v open >/dev/null 2>&1; then
  open "$PRESENT_URL" || true
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$PRESENT_URL" || true
fi
printf 'Presented view: %s\n' "$PRESENT_URL"
```

## Validation checklist before storing

- Exactly one `createSurface` for the surface you intend to render.
- `catalogId` is `https://cpk-a2ui.local/catalogs/copilotkit/v1`.
- The first rendered component is reachable from `root` through child refs.
- Every `child` and `children` reference points to an existing component `id`.
- Component names exist in `src/a2ui/catalog/definitions.ts`.
- Markdown strings are JSON-escaped (`\n`, not raw multiline strings inside JSON).
- Source links are normal Markdown links, not raw HTML/script.
- The outer artifact request uses the key `a2ui`, not `envelope`, `kind`, or
  `a2ui_operations` at the top level.
- Store response has `artifact_id` and `version`.
- Public present response has only `a2ui` and `expires_at`.

## Common failures

- **Empty presentation:** no `createSurface`, or `surfaceId` mismatch between
  operations.
- **Missing nodes:** a `children`/`child` id has no corresponding component.
- **Nothing renders:** invented component name or wrong catalog id.
- **400/422 on store:** body was not valid JSON or omitted the outer `a2ui` key.
- **409 on store:** duplicate artifact slug; suffix the slug.
- **Unsafe output:** model-generated HTML/script. Use `Markdown` text and links;
  do not ask the renderer to execute arbitrary code.
