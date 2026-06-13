import Link from "next/link";
import { SiteNav, PageHeader } from "@/components/pdf-analyst/Brand";

export default function Home() {
  return (
    <>
      <SiteNav active="home" />
      <PageHeader
        eyebrow="Agent-first generative UI"
        meta={
          <span className="pill">
            <span className="dot" /> BYOT cert-auth demo
          </span>
        }
        title={
          <>
            A team of agents co-authors text, researches the web, and
            <br className="hidden md:inline" />
            <span
              className="bg-clip-text text-transparent"
              style={{ backgroundImage: "var(--brand-gradient)" }}
            >
              presents cited A2UI.
            </span>
          </>
        }
        subtitle="Agent A and Agent B write team-scoped documents with real AWID/BYOT certificates. The team's concierge researches the live web with LinkUp, paints a cited A2UI surface, and mints a safe no-login link for the human."
      />

      <main className="flex-1 max-w-[1320px] mx-auto px-6 py-12 w-full">
        <div className="grid md:grid-cols-2 gap-5">
          <ModeCard
            href="/fixed"
            badge="01 · TEAM TEXT"
            title="Shared text, real authors"
            blurb="Every document endpoint is scoped to the verified team certificate. Each version records which agent signed the request."
            bullets={[
              "Agent A creates the team memo over AWID team-auth",
              "Agent B appends a new immutable version",
              "The response shows alias, address, DID, and certificate attribution",
            ]}
            cta="Open the team workspace"
          />
          <ModeCard
            href="/dynamic"
            badge="02 · CONCIERGE"
            title="Live research → safe link"
            blurb="The concierge researches the topic with LinkUp, asks Gemini to compose the surface, then stores and presents the A2UI artifact."
            bullets={[
              "Real LinkUp web search — not a server-side search shortcut",
              "Markdown summary plus source list render as catalog components",
              "present_to_human mints a no-login /present token for the human",
            ]}
            cta="Open the concierge"
          />
        </div>

        <section className="mt-6 grid lg:grid-cols-[1.1fr_0.9fr] gap-5">
          <div className="surface p-7">
            <span className="mono text-[11px] uppercase tracking-[0.14em] text-[var(--muted-2)]">
              What this demo proves
            </span>
            <h2 className="text-[24px] font-semibold tracking-tight mt-2">
              BYOT identity is the product boundary; A2UI is the human interface.
            </h2>
            <p className="mt-3 text-[15px] leading-relaxed text-[var(--ink-2)]">
              The server trusts AWID team certificates, not browser sessions. Agents
              can co-author plain text as verified team members, while a concierge
              turns live web research into a renderer-safe A2UI artifact. Humans
              receive a capability link that renders the cited surface without an
              account or login.
            </p>
          </div>
          <div className="surface-soft p-7">
            <span className="mono text-[11px] uppercase tracking-[0.14em] text-[var(--muted-2)]">
              Recordable flow
            </span>
            <ol className="mt-3 space-y-2 text-[14px] leading-relaxed text-[var(--ink-2)]">
              <li><strong>1.</strong> Agent A creates a memo; Agent B appends a version.</li>
              <li><strong>2.</strong> The operator asks the concierge to research the topic.</li>
              <li><strong>3.</strong> The canvas fills with cards, markdown, and source links.</li>
              <li><strong>4.</strong> The concierge mints a safe <code className="mono">/present</code> link.</li>
              <li><strong>5.</strong> A fresh browser opens the link; a bogus token returns 404.</li>
            </ol>
          </div>
        </section>

        <section className="mt-14">
          <div className="flex items-end justify-between mb-4">
            <div>
              <span className="mono text-[11px] uppercase tracking-[0.14em] text-[var(--muted-2)]">
                The design system
              </span>
              <h2 className="text-[22px] font-semibold tracking-tight mt-1">
                22 components, one catalog
              </h2>
            </div>
            <Link
              href="/catalog"
              className="mono text-[12px] text-[var(--ink)] hover:text-[var(--lilac)] transition"
            >
              See them all →
            </Link>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {CATALOG_GROUPS.flatMap((g) =>
              g.items.map((name) => (
                <div
                  key={name}
                  className="surface px-3 py-3 text-[13px] flex items-center justify-between"
                >
                  <span className="mono uppercase tracking-wider text-[11px] text-[var(--muted-2)]">
                    {g.short}
                  </span>
                  <span className="font-medium text-[var(--ink)]">{name}</span>
                </div>
              )),
            )}
          </div>
        </section>

        <section className="mt-14 grid md:grid-cols-3 gap-3">
          <Spec
            k="Frontend"
            v="Next.js 16 · React 19 · Tailwind v4 · @copilotkit/react-core/v2"
          />
          <Spec
            k="Bridge"
            v="@copilotkit/runtime (v2) · @ag-ui/client · a2ui middleware"
          />
          <Spec
            k="Backend"
            v="Python · LangChain · LangGraph · FastAPI · ag-ui-langgraph"
          />
        </section>
      </main>

      <footer className="border-t border-[var(--line)] py-6 mt-10">
        <div className="max-w-[1320px] mx-auto px-6 text-xs text-[var(--muted)] flex items-center justify-between">
          <span>
            Drop your design tokens into{" "}
            <code className="mono px-1.5 py-0.5 rounded bg-[var(--surface-soft)] border border-[var(--line)] text-[11px]">
              src/a2ui/theme.css
            </code>{" "}
            to re-skin every surface.
          </span>
          <span className="mono">v0.2</span>
        </div>
      </footer>
    </>
  );
}

const CATALOG_GROUPS = [
  {
    short: "LAY",
    items: ["Stack", "Row", "Grid", "Card", "Section", "Divider"],
  },
  {
    short: "TXT",
    items: ["Heading", "Text", "Markdown", "Overline", "Badge", "Callout", "BulletList"],
  },
  {
    short: "DATA",
    items: [
      "StatCard",
      "BarChart",
      "HorizontalBarChart",
      "LineChart",
      "DonutChart",
      "ScatterChart",
      "DataTable",
    ],
  },
  { short: "ACT", items: ["Button", "ChoiceChips"] },
];

function ModeCard({
  href,
  badge,
  title,
  blurb,
  bullets,
  cta,
}: {
  href: string;
  badge: string;
  title: string;
  blurb: string;
  bullets: string[];
  cta: string;
}) {
  return (
    <Link
      href={href}
      className="group surface p-7 hover:border-[var(--lilac)] transition relative overflow-hidden"
    >
      <div className="absolute -top-20 -right-20 w-[260px] h-[260px] rounded-full brand-gradient-soft opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="relative">
        <span className="mono text-[11px] uppercase tracking-[0.14em] text-[var(--muted-2)]">
          {badge}
        </span>
        <h3 className="text-[24px] font-semibold tracking-tight mt-2">
          {title}
        </h3>
        <p className="mt-3 text-[var(--muted)] leading-relaxed text-[15px]">
          {blurb}
        </p>
        <ul className="mt-5 space-y-2">
          {bullets.map((b) => (
            <li
              key={b}
              className="flex items-start gap-2.5 text-[13.5px] text-[var(--ink-2)]"
            >
              <span className="mt-2 w-1.5 h-1.5 rounded-full bg-[var(--lilac)] flex-none" />
              <span>{b}</span>
            </li>
          ))}
        </ul>
        <span className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-[var(--ink)] group-hover:text-[var(--ink)] transition mono">
          {cta} <span aria-hidden>→</span>
        </span>
      </div>
    </Link>
  );
}

function Spec({ k, v }: { k: string; v: string }) {
  return (
    <div className="surface-soft p-4">
      <div className="mono text-[11px] uppercase tracking-[0.14em] text-[var(--muted-2)]">
        {k}
      </div>
      <div className="mt-1 text-[13px] text-[var(--ink-2)]">{v}</div>
    </div>
  );
}
