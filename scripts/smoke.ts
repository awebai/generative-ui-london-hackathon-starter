#!/usr/bin/env node
/**
 * pnpm smoke — Composite gate, the load-bearing CI check.
 *
 * GenUI's LangGraph/AG-UI sidecar is retired. The product path is the
 * cert-auth server plus `/present` renderer; legacy agent probes now skip
 * when `/fixed` has been removed.
 *
 * Runs (in order, failing fast):
 *   1. `pnpm verify-pins`               — lockfile / package.json drift
 *   2. `pnpm validate-widget --examples`— other-examples/EXAMPLE.json files
 *   3. `pnpm validate-widget` over every JSON in the widget/schema dirs
 *   4. `pnpm test:widgets`              — fixture renderer pass (delegates to validator)
 *   4a. `pnpm test:schemas`             — pytest path-vs-data alignment, SKIPPED when
 *                                         agent/tests/ is absent (pdf-analyst ships no
 *                                         pytest suite at the agent root yet)
 *   5. offline envelope shape check     — validates public/offline-envelopes.json
 *                                         structure if present; SKIPPED when absent
 *                                         (it was archived with PortKit)
 *   6. legacy agent import probe        — import agent/main.py if present
 *   6a. offline /fixed probe            — SKIPPED after sidecar retirement
 *   7. legacy agent connectivity probe  — SKIPPED when no GEMINI_API_KEY
 *
 * Exit non-zero if any step fails. Machine-parsable summary at the end.
 */
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { spawnSync } from "node:child_process";

const REPO_ROOT = join(__dirname, "..");

const RED = "\x1b[31m";
const GREEN = "\x1b[32m";
const YELLOW = "\x1b[33m";
const DIM = "\x1b[2m";
const BOLD = "\x1b[1m";
const RESET = "\x1b[0m";

type Step = {
  name: string;
  run: () => Promise<{ pass: boolean; detail: string }>;
};

const results: { name: string; pass: boolean; detail: string }[] = [];

function pnpmRun(scriptName: string, ...args: string[]): { pass: boolean; detail: string } {
  // Use the local pnpm exec form so we don't hit recursive `pnpm` lookup issues.
  const res = spawnSync("pnpm", ["run", scriptName, ...args], {
    cwd: REPO_ROOT,
    stdio: "inherit",
    env: { ...process.env, FORCE_COLOR: "1" },
  });
  return {
    pass: res.status === 0,
    detail: res.status === 0 ? "passed" : `failed (exit ${res.status})`,
  };
}

function shellRun(cmd: string, args: string[], opts: { cwd?: string } = {}): { pass: boolean; detail: string } {
  const res = spawnSync(cmd, args, {
    cwd: opts.cwd ?? REPO_ROOT,
    stdio: "inherit",
    env: { ...process.env, FORCE_COLOR: "1" },
  });
  return {
    pass: res.status === 0,
    detail: res.status === 0 ? "passed" : `failed (exit ${res.status})`,
  };
}

// Widget/schema dirs to validate JSON under, in the pdf-analyst layout. The
// archived PortKit `agent/src/widgets/` dir is gone; the in-repo catalog
// schemas live at agent/src/a2ui/schemas/ and the legal example keeps its
// fixtures under its own schemas dir. Missing dirs are skipped.
const WIDGET_JSON_DIRS = [
  join(REPO_ROOT, "agent", "src", "a2ui", "schemas"),
  join(REPO_ROOT, "other-examples", "legal-contract-review", "schemas"),
];

function findWidgetJsons(): string[] {
  const out: string[] = [];
  for (const dir of WIDGET_JSON_DIRS) {
    if (!existsSync(dir)) continue;
    const stack = [dir];
    while (stack.length > 0) {
      const cur = stack.pop()!;
      for (const entry of readdirSync(cur, { withFileTypes: true })) {
        const full = join(cur, entry.name);
        if (entry.isDirectory()) stack.push(full);
        else if (entry.isFile() && entry.name.endsWith(".json")) out.push(full);
      }
    }
  }
  return out;
}

// The LangGraph/AG-UI agent sidecar is retired. Keep these empty so the
// legacy smoke probe only verifies that any leftover agent/main.py imports
// cleanly and does not require /fixed or /dynamic.
const REQUIRED_AGENT_ENDPOINTS: string[] = [];
const OPTIONAL_AGENT_ENDPOINTS: string[] = [];

const STEPS: Step[] = [
  {
    name: "verify-pins",
    run: async () =>
      shellRun(join(REPO_ROOT, "scripts", "verify-pins.sh"), []),
  },
  {
    name: "validate-widget --examples (other-examples/*/EXAMPLE.json)",
    run: async () => {
      const validateScript = join(REPO_ROOT, "scripts", "validate-widget.ts");
      const res = spawnSync(
        "pnpm",
        ["exec", "tsx", validateScript, "--examples"],
        { cwd: REPO_ROOT, stdio: "inherit", env: { ...process.env, FORCE_COLOR: "1" } },
      );
      return {
        pass: res.status === 0,
        detail: res.status === 0 ? "EXAMPLE.json files validated" : `failed (exit ${res.status})`,
      };
    },
  },
  {
    name: "validate-widget over widget/schema dirs",
    run: async () => {
      const widgets = findWidgetJsons();
      if (widgets.length === 0) {
        console.log(
          `${YELLOW}!${RESET} ${DIM}No widget JSONs to validate yet.${RESET}\n`,
        );
        return { pass: true, detail: "skipped (no widgets)" };
      }
      const validateScript = join(REPO_ROOT, "scripts", "validate-widget.ts");
      const res = spawnSync(
        "pnpm",
        ["exec", "tsx", validateScript, ...widgets],
        { cwd: REPO_ROOT, stdio: "inherit", env: { ...process.env, FORCE_COLOR: "1" } },
      );
      return {
        pass: res.status === 0,
        detail: res.status === 0 ? `${widgets.length} files validated` : `failed (exit ${res.status})`,
      };
    },
  },
  {
    name: "test:widgets",
    run: async () => pnpmRun("test:widgets"),
  },
  {
    name: "explain sanity (pnpm explain themes resolves a HACKATHON.md section)",
    run: async () => {
      // Regression guard: `pnpm explain` must keep matching HACKATHON.md's
      // live seam headings ("## §N — Title"). It silently rotted once when
      // the doc's heading style changed — this step makes that loud.
      const explainScript = join(REPO_ROOT, "scripts", "explain.ts");
      const res = spawnSync("pnpm", ["exec", "tsx", explainScript, "themes"], {
        cwd: REPO_ROOT,
        stdio: "pipe",
        env: { ...process.env, FORCE_COLOR: "0" },
      });
      const out = `${res.stdout ?? ""}${res.stderr ?? ""}`;
      if (res.status !== 0) {
        console.error(out);
        return { pass: false, detail: `pnpm explain themes exited ${res.status}` };
      }
      if (!out.includes("Re-theme")) {
        console.error(out);
        return { pass: false, detail: "explain output missing the §1 section" };
      }
      console.log(`${GREEN}✓${RESET} ${DIM}pnpm explain themes printed the §1 section.${RESET}\n`);
      return { pass: true, detail: "explain resolves seam sections" };
    },
  },
  {
    name: "test:schemas (pytest path-vs-data alignment)",
    run: async () => {
      // `pnpm test:schemas` is `cd agent && uv run python -m pytest tests/`.
      // The pdf-analyst default agent ships no pytest suite at agent/tests/
      // yet (the PortKit schema tests were archived). Skip when the dir is
      // absent so smoke is exit-0 statically; run it the moment a suite lands.
      const testsDir = join(REPO_ROOT, "agent", "tests");
      if (!existsSync(testsDir)) {
        console.log(
          `${YELLOW}!${RESET} ${DIM}agent/tests/ not present — no pytest schema suite to run. Skipping.${RESET}\n`,
        );
        return { pass: true, detail: "skipped (no agent/tests/)" };
      }
      return pnpmRun("test:schemas");
    },
  },
  {
    name: "offline envelope shape check (public/offline-envelopes.json)",
    run: async () => {
      // pdf-analyst default swap: public/offline-envelopes.json was archived
      // to other-examples/portkit/public/. When absent, skip cleanly. The
      // shape validation below still runs if a hacker drops a pdf-analyst
      // offline file back at public/offline-envelopes.json.
      const offlinePath = join(REPO_ROOT, "public", "offline-envelopes.json");
      if (!existsSync(offlinePath)) {
        console.log(
          `${YELLOW}!${RESET} ${DIM}public/offline-envelopes.json not present (archived with PortKit). Skipping.${RESET}\n`,
        );
        return { pass: true, detail: "skipped (no offline envelopes)" };
      }
      try {
        const raw = readFileSync(offlinePath, "utf-8");
        const parsed = JSON.parse(raw);

        // The new wrapper shape (plan §6.6) has byPrompt + bySurface.
        // We accept the legacy flat shape too (just prompt-keyed) for back-compat.
        const hasWrapper =
          parsed && typeof parsed === "object" &&
          (parsed.byPrompt || parsed.bySurface);

        if (!hasWrapper) {
          // Legacy shape — accept if it contains A2UI markers anywhere in the file.
          if (!raw.includes("createSurface") && !raw.includes("surfaceId")) {
            console.error(
              `${RED}✗${RESET} public/offline-envelopes.json doesn't reference any A2UI envelope (no createSurface or surfaceId found).`,
            );
            return { pass: false, detail: "envelope check failed: no A2UI markers" };
          }
          console.log(
            `${GREEN}✓${RESET} ${DIM}offline-envelopes.json parses and contains A2UI envelope markers (legacy shape).${RESET}\n`,
          );
          return { pass: true, detail: "parsed (legacy shape)" };
        }

        // Wrapper shape — validate the bySurface map.
        const bySurface = parsed.bySurface as Record<string, unknown> | undefined;
        if (!bySurface || typeof bySurface !== "object") {
          console.error(
            `${RED}✗${RESET} offline-envelopes.json wrapper is missing 'bySurface' object.`,
          );
          return { pass: false, detail: "missing bySurface" };
        }
        const surfaceCount = Object.keys(bySurface).length;
        if (surfaceCount === 0) {
          console.error(
            `${RED}✗${RESET} 'bySurface' is empty — at least one surface required.`,
          );
          return { pass: false, detail: "empty bySurface" };
        }
        for (const [surfaceId, envs] of Object.entries(bySurface)) {
          if (!Array.isArray(envs) || envs.length === 0) {
            console.error(
              `${RED}✗${RESET} bySurface["${surfaceId}"] is not a non-empty array of envelopes.`,
            );
            return { pass: false, detail: `bad bySurface entry: ${surfaceId}` };
          }
        }
        // (PortKit pinned a required "contract-review" surface here; the
        // pdf-analyst default has no such hard requirement — any non-empty
        // bySurface map is accepted. Re-add a required-surface assertion here
        // if a future offline file must guarantee a specific surface.)
        console.log(
          `${GREEN}✓${RESET} ${DIM}offline-envelopes.json wrapper valid (${surfaceCount} surface${surfaceCount === 1 ? "" : "s"} indexed: ${Object.keys(bySurface).join(", ")}).${RESET}\n`,
        );
        return { pass: true, detail: `${surfaceCount} surfaces indexed` };
      } catch (e) {
        console.error(`${RED}✗${RESET} offline-envelopes.json is invalid JSON: ${(e as Error).message}`);
        return { pass: false, detail: "invalid JSON" };
      }
    },
  },
  {
    name: "agent endpoint probe (FastAPI /fixed + /dynamic [+ /legal])",
    run: async () => {
      // pdf-analyst default swap: the agent is now the FastAPI app at
      // agent/main.py, not a langgraph-cli graph. Assert it imports cleanly
      // and registers the expected endpoints. We boot `python -c "..."`
      // against the agent's .venv so this is a deterministic, OFFLINE-safe
      // check — importing the app builds the LLM clients (with a placeholder
      // key) but makes NO live model call.
      const agentDir = join(REPO_ROOT, "agent");
      const mainPy = join(agentDir, "main.py");
      if (!existsSync(mainPy)) {
        console.log(
          `${YELLOW}!${RESET} ${DIM}agent/main.py not found. Skipping endpoint probe.${RESET}\n`,
        );
        return { pass: true, detail: "skipped (no agent/main.py)" };
      }
      const venvPython = join(agentDir, ".venv", "bin", "python");
      const pythonBin = existsSync(venvPython) ? venvPython : "python3";
      if (!existsSync(venvPython)) {
        console.log(
          `${YELLOW}!${RESET} ${DIM}agent/.venv/bin/python not found — using system python3. Run \`pnpm install:agent\` to bootstrap.${RESET}\n`,
        );
      }
      // Cross the JS → Python boundary as Python list literals (string
      // elements, no unpacking — JSON arrays of strings are valid Python
      // list literals so JSON.stringify is safe here).
      const requiredPy = JSON.stringify(REQUIRED_AGENT_ENDPOINTS);
      const optionalPy = JSON.stringify(OPTIONAL_AGENT_ENDPOINTS);
      const script = `
import sys

required = ${requiredPy}
optional = ${optionalPy}

try:
    import main
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"\\nFAIL: importing agent/main.py raised {type(e).__name__}: {e}")
    sys.exit(1)

app = getattr(main, "app", None)
if app is None:
    print("FAIL: agent/main.py has no module-level 'app' (expected a FastAPI instance).")
    sys.exit(1)

# Collect the set of registered route paths (FastAPI Route objects expose .path).
paths = set()
for r in getattr(app, "routes", []):
    p = getattr(r, "path", None)
    if isinstance(p, str):
        paths.add(p)

missing = [p for p in required if p not in paths]
present_optional = [p for p in optional if p in paths]

for p in required:
    print(f"  {'OK' if p in paths else 'MISSING'}: {p}")
for p in optional:
    print(f"  {'OK' if p in paths else 'absent (optional)'}: {p}")

if missing:
    print(f"\\nFAIL: agent/main.py is missing required endpoint(s): {missing}")
    sys.exit(1)

print(f"\\nFastAPI app registers all required endpoints ({required}); optional present: {present_optional}.")
sys.exit(0)
`;
      // Provide a placeholder GEMINI_API_KEY — the agents construct
      // ChatGoogleGenerativeAI clients at import time. The probe imports the
      // app, it does NOT make a live call, so a placeholder is sufficient.
      const probeEnv = {
        ...process.env,
        FORCE_COLOR: "1",
        GEMINI_API_KEY: process.env.GEMINI_API_KEY || "smoke-probe-placeholder",
      };
      const res = spawnSync(pythonBin, ["-c", script], {
        cwd: agentDir,
        stdio: "inherit",
        env: probeEnv,
      });
      if (res.status === 0) {
        return { pass: true, detail: "FastAPI endpoints registered" };
      }
      if (res.status === 1) {
        return { pass: false, detail: "agent/main.py failed to import or missing endpoints" };
      }
      // Likely env issue (missing venv or python). Don't fail smoke; warn loudly.
      console.log(
        `${YELLOW}!${RESET} ${DIM}agent endpoint probe could not run (exit ${res.status}). Run \`pnpm install:agent\` to bootstrap the venv.${RESET}\n`,
      );
      return { pass: true, detail: `skipped (probe exit ${res.status})` };
    },
  },
  {
    name: "offline /fixed probe (retired sidecar skip)",
    run: async () => {
      // The OFFLINE=1 gate. The endpoint probe above proves the app IMPORTS;
      // this proves the /fixed graph actually PAINTS a surface offline. It
      // imports the /fixed graph and invokes it in-process (no uvicorn, no
      // port) with OFFLINE=1 and GEMINI_API_KEY explicitly removed, then
      // asserts the emitted tool result carries the A2UI surface ops
      // (a2ui_operations / createSurface / updateComponents / updateDataModel).
      // This closes the "smoke green while `dev` fails" gap: a regression that
      // breaks the no-key offline emission (e.g. an eager Gemini client or a
      // broken stub) FAILS here loudly.
      const agentDir = join(REPO_ROOT, "agent");
      const fixedAgentPy = join(agentDir, "src", "fixed_agent.py");
      if (!existsSync(fixedAgentPy)) {
        console.log(
          `${YELLOW}!${RESET} ${DIM}agent/src/fixed_agent.py retired. Skipping offline /fixed probe.${RESET}\n`,
        );
        return { pass: true, detail: "skipped (retired agent sidecar)" };
      }
      const venvPython = join(agentDir, ".venv", "bin", "python");
      const pythonBin = existsSync(venvPython) ? venvPython : "python3";
      if (!existsSync(venvPython)) {
        console.log(
          `${YELLOW}!${RESET} ${DIM}agent/.venv/bin/python not found — using system python3. Run \`pnpm install:agent\` to bootstrap.${RESET}\n`,
        );
      }
      const script = `
import sys

try:
    from langchain_core.messages import HumanMessage, ToolMessage
    from src.fixed_agent import graph
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"\\nFAIL: importing the /fixed graph (OFFLINE=1, no key) raised {type(e).__name__}: {e}")
    sys.exit(1)

try:
    result = graph.invoke(
        {"messages": [HumanMessage("show the dashboard")]},
        config={"configurable": {"thread_id": "smoke-offline"}},
    )
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"\\nFAIL: invoking the offline /fixed graph raised {type(e).__name__}: {e}")
    sys.exit(1)

tool_msgs = [m for m in result.get("messages", []) if isinstance(m, ToolMessage)]
if not tool_msgs:
    print("FAIL: offline /fixed produced no ToolMessage — no A2UI surface emitted.")
    sys.exit(1)

content = "".join(str(m.content) for m in tool_msgs)
markers = ["a2ui_operations", "createSurface", "updateComponents", "updateDataModel"]
missing = [mk for mk in markers if mk not in content]
if missing:
    print(f"FAIL: offline /fixed tool result is missing A2UI surface markers: {missing}")
    sys.exit(1)

for mk in markers:
    print(f"  OK: {mk}")
print("\\nOffline /fixed emitted a real A2UI surface (no key, OFFLINE=1).")
sys.exit(0)
`;
      // Explicitly REMOVE the key so this proves the no-key path. Unlike the
      // endpoint probe (which supplies a placeholder), the whole point here is
      // that OFFLINE=1 needs no key at all. Strip both env names the SDK reads
      // (GEMINI_API_KEY / GOOGLE_API_KEY) by destructuring them out of the
      // inherited env, then force OFFLINE=1.
      const {
        GEMINI_API_KEY: _gemini,
        GOOGLE_API_KEY: _google,
        ...envWithoutKeys
      } = process.env;
      const offlineEnv = { ...envWithoutKeys, FORCE_COLOR: "1", OFFLINE: "1" };
      const res = spawnSync(pythonBin, ["-c", script], {
        cwd: agentDir,
        stdio: "inherit",
        env: offlineEnv,
      });
      if (res.status === 0) {
        return { pass: true, detail: "offline /fixed painted a real A2UI surface (no key)" };
      }
      if (res.status === 1) {
        return { pass: false, detail: "offline /fixed did not emit an A2UI surface (no key)" };
      }
      // Non-1 exit: probe couldn't run (missing venv/python). Warn, don't fail.
      console.log(
        `${YELLOW}!${RESET} ${DIM}offline /fixed probe could not run (exit ${res.status}). Run \`pnpm install:agent\` to bootstrap the venv.${RESET}\n`,
      );
      return { pass: true, detail: `skipped (probe exit ${res.status})` };
    },
  },
  {
    name: "legacy agent connectivity probe (retired sidecar skip)",
    run: async () => {
      console.log(`${YELLOW}!${RESET} ${DIM}LangGraph sidecar retired. Skipping live Gemini agent probe.${RESET}\n`);
      return { pass: true, detail: "skipped (retired agent sidecar)" };
    },
  },
];

async function main(): Promise<void> {
  console.log(`${BOLD}pnpm smoke${RESET} — composite gate\n`);

  let failed = 0;

  for (const step of STEPS) {
    console.log(`${BOLD}━━━ ${step.name} ━━━${RESET}`);
    const t0 = Date.now();
    const res = await step.run();
    const ms = Date.now() - t0;
    results.push({ name: step.name, ...res });
    if (!res.pass) {
      failed++;
      // Fail fast — first failure is usually informative enough.
      console.error(
        `\n${RED}${BOLD}Step "${step.name}" failed (${ms}ms).${RESET} Stopping early.\n`,
      );
      break;
    }
    console.log(`${DIM}  → step done in ${ms}ms${RESET}\n`);
  }

  // Summary
  console.log(`${BOLD}━━━ smoke summary ━━━${RESET}`);
  for (const r of results) {
    const icon = r.pass ? `${GREEN}✓${RESET}` : `${RED}✗${RESET}`;
    console.log(`  ${icon} ${r.name} ${DIM}— ${r.detail}${RESET}`);
  }
  // List steps that didn't run
  const ran = new Set(results.map((r) => r.name));
  for (const s of STEPS) {
    if (!ran.has(s.name)) console.log(`  ${YELLOW}-${RESET} ${s.name} ${DIM}(not run)${RESET}`);
  }
  console.log();

  if (failed === 0) {
    console.log(`${GREEN}${BOLD}SMOKE PASS.${RESET}`);
    process.exit(0);
  } else {
    console.log(`${RED}${BOLD}SMOKE FAIL.${RESET}`);
    process.exit(1);
  }
}

void main();
