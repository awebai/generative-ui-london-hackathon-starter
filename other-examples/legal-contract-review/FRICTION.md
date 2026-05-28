# Friction Log — Legal Contract Review

Built as a dogfooding exercise per [plan §0.6](https://www.notion.so/36e3aa38185281e49674f95ea7039b90). Every row converts to a GitHub issue with the `dogfood-friction` label (see plan §0.7 for the label taxonomy + triage cadence).

The engineer building this example is a **proxy hackathon attendee**: documented paths only (`pnpm new-widget`, `create-a2ui-widget` skill, `AGENTS.md`, in-tree READMEs, validators), AI coding assistant for the typing, no insider help from starter authors. If a documented path doesn't unblock you, that *is* the issue — log it here.

End of each build day (17:00): convert every row in **Open** to a GitHub issue via the `to-issues` skill, then move it to **Converted to issues**.

---

## Row template

Each row uses the §0.7 template:

```markdown
## [P0/P1/P2] One-line title
- **Encountered while:** [step from create-a2ui-widget skill / this plan / AGENTS.md section]
- **What I tried:** [the documented path]
- **What happened:** [error / confusion / missing piece — paste actual error if any]
- **What I wanted:** [the right outcome]
- **Suggested fix:** [if obvious; else "needs design"]
- **Who hits this:** [hackathon attendee profile — Claude Code / Gemini CLI / Cursor / human-only / new-to-LangGraph / etc.]
- **Filed as:** [#NNN]
```

Severities (from §0.7):

- **P0 / `severity:P0-blocker`** — hacker cannot proceed via documented path
- **P1 / `severity:P1-pain`** — works but with significant unintended difficulty
- **P2 / `severity:P2-polish`** — minor wording, error-message clarity, doc gaps

---

## Open

_New friction rows land here. Move to "Converted to issues" once filed via `gh`._

---

## Converted to issues

_Rows that have been filed as GitHub issues. Keep the row body for transparency; update `Filed as:` with the issue number._
