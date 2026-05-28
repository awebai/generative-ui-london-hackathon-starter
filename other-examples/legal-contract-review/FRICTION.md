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
- **P3 / `severity:P3-nice-to-have`** — minor polish; lower priority than P2

---

## Open

_(empty — all rows filed in the post-Wave-2 batch on 2026-05-28)_

---

## Converted to issues

### [P0] pnpm validate-widget rejects shipped flight_card.json (wrapper shape mismatch)
- **Filed as:** [#2](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/2)
- **Discovered by:** B6 (Wave 1 blitz, 2026-05-28)

### [P0] pnpm test:widgets red day-one — shipped fixture shapes don't match validator
- **Filed as:** [#3](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/3)
- **Discovered by:** B6 (Wave 1 blitz, 2026-05-28)

### [P0] Plan §6.1 langgraph multi-graph fix is incomplete — relative imports break under path-based loader
- **Filed as:** [#4](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/4)
- **Discovered by:** B5 (Wave 1 blitz, 2026-05-28)
- **Workaround applied:** sys.path injection in `other-examples/legal-contract-review/agent/graph.py` with absolute imports

### [P1] lefthook 'Can't find lefthook in PATH' on every commit from a worktree (cross-cutting)
- **Filed as:** [#5](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/5)
- **Discovered by:** B1, B2, B3, B4, B4-finalize, B5, B6 — 5/5 commit operations. Escalated from P2 → P1 due to universal hit rate.

### [P1] Three incompatible "fixture" shapes coexist in the starter
- **Filed as:** [#16](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/16)
- **Discovered by:** B6 (Wave 1 blitz, 2026-05-28)

### [P1] validate-widget error messages point at .py file instead of canonical JSON
- **Filed as:** [#17](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/17)
- **Discovered by:** B6 (Wave 1 blitz, 2026-05-28)

### [P1] Heavy blitz slots risk mid-flight context exhaustion
- **Filed as:** [#18](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/18)
- **Discovered by:** B4 + B4-finalize + B7 (Wave 1 and Wave 2 of blitz, 2026-05-28). CONFIRMED by 2 independent data points (B4 9-component catalog, B7 4-file wiring).

### [P2] PLAN.md in-tree doesn't have §0.7 (friction protocol) — only Notion has it
- **Filed as:** [#6](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/6)
- **Discovered by:** B1 (Wave 1 blitz, 2026-05-28)

### [P2] No template file or generator for sub-repo layout
- **Filed as:** [#7](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/7)
- **Discovered by:** B2 (Wave 1 blitz, 2026-05-28)

### [P2] tsc not available from worktree path
- **Filed as:** [#8](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/8)
- **Discovered by:** B3 (Wave 1 blitz, 2026-05-28)

### [P2] pnpm dev:ui cannot smoke-test changes in a worktree
- **Filed as:** [#9](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/9)
- **Discovered by:** B3 (Wave 1 blitz, 2026-05-28)

### [P2] No documented convention for the widget-mirror-vs-canonical-location question
- **Filed as:** [#10](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/10)
- **Discovered by:** B6 (Wave 1 blitz, 2026-05-28)

### [P2] node_modules not pre-installed in fresh worktree
- **Filed as:** [#11](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/11)
- **Discovered by:** B6 (Wave 1 blitz, 2026-05-28)

### [P2] langgraph 0.7.101 dockerfile mis-routes second dependency's graph path
- **Filed as:** [#12](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/12)
- **Discovered by:** B5 (Wave 1 blitz, 2026-05-28)

### [P3] AC1 grep ambiguity — grep 'CopilotKit' matches brand text vs provider
- **Filed as:** [#13](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/13)
- **Discovered by:** B3 (Wave 1 blitz, 2026-05-28)

### [P3] Worktree-aware env loading for langgraph
- **Filed as:** [#14](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/14)
- **Discovered by:** B5 (Wave 1 blitz, 2026-05-28)

### [P3] setuptools auto-discovery package name collision
- **Filed as:** [#15](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/15)
- **Discovered by:** B5 (Wave 1 blitz, 2026-05-28)

### [P2] Starter ships with red typecheck baseline (5 pre-existing TS errors)
- **Filed as:** [#19](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/19)
- **Discovered by:** B9 (Wave 2 blitz, 2026-05-28)
- **Notes:** 5 pre-existing TS errors in `docker-route-override.ts`, `src/app/declarative-generative-ui/renderers.tsx`, `src/components/generative-ui/charts/bar-chart.tsx`. Makes "is my change clean?" a grep-on-paths exercise instead of an exit-code check.

### [P2] '*/' inside a JSDoc /** ... */ block terminates the comment early (esbuild fails)
- **Filed as:** [#20](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/20)
- **Discovered by:** B8 (Wave 2 blitz, 2026-05-28)
- **Notes:** Hit while writing `other-examples/*/EXAMPLE.json` in a comment header. AGENTS.md style note or skill-authoring note would prevent.

### [P2] JSON.stringify of object array embeds as objects (not tuples) into Python via TS template string
- **Filed as:** [#21](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/21)
- **Discovered by:** B8 (Wave 2 blitz, 2026-05-28)
- **Notes:** Caused `ValueError: not enough values to unpack` on first smoke run. Trivial fix once seen but easy to miss when crossing JS/Python boundary. Suggested: `toPythonTuples()` helper if more shell-out coming.

### [P3] ChatOpenAI() raises at construction time when OPENAI_API_KEY is missing
- **Filed as:** [#22](https://github.com/jerelvelarde/london-a2ui-a2a-starter/issues/22)
- **Discovered by:** B8 (Wave 2 blitz, 2026-05-28)
- **Notes:** Any health-check that imports an agent module needs an env-var workaround. Smoke uses a placeholder. Document in `agent/src/widgets/README.md` or a "probing the agents" runbook.
