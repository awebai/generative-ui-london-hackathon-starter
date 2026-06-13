import { PresentSurface } from "./PresentSurface";

type A2UIOp = Record<string, unknown>;
type PresentResponse = { a2ui: unknown; expires_at: string };

type PresentPageProps = {
  params: Promise<{ token: string }>;
};

export default async function PresentPage({ params }: PresentPageProps) {
  const { token } = await params;
  const operations = await fetchPresentation(token);

  if (!operations) {
    return <LinkUnavailable />;
  }

  return (
    <main className="min-h-screen bg-[var(--bg)] px-4 py-8 text-[var(--ink)] md:px-8">
      <div className="mx-auto flex max-w-5xl flex-col gap-5">
        <header className="flex flex-col gap-2">
          <p className="mono text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--lilac)]">
            Agent presentation
          </p>
          <h1 className="text-[28px] font-semibold tracking-[-0.04em] md:text-[36px]">
            Shared surface
          </h1>
          <p className="max-w-2xl text-[14px] leading-relaxed text-[var(--muted)]">
            This read-only link was minted by an authenticated team agent. No
            account or login is required; possession of the link grants access
            only to this surface.
          </p>
        </header>
        <section className="a2ui-surface rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-4 shadow-[0_16px_50px_rgba(10,10,20,0.08)] md:p-6">
          <PresentSurface operations={operations} />
        </section>
      </div>
    </main>
  );
}

async function fetchPresentation(token: string): Promise<A2UIOp[] | null> {
  let response: Response;
  try {
    response = await fetch(
      `${serverOrigin()}/present/${encodeURIComponent(token)}`,
      { cache: "no-store" },
    );
  } catch (err) {
    console.warn("[present] failed to fetch presentation", err);
    return null;
  }

  if (response.status === 404) return null;
  if (!response.ok) {
    console.warn("[present] server returned", response.status);
    return null;
  }

  const data: unknown = await response.json();
  if (!isPresentResponse(data)) return null;
  return normalizeA2UI(data.a2ui);
}

function serverOrigin() {
  return (process.env.SERVER_ORIGIN ?? "http://localhost:8200").replace(/\/$/, "");
}

function normalizeA2UI(a2ui: unknown): A2UIOp[] | null {
  if (Array.isArray(a2ui)) return a2ui as A2UIOp[];
  if (!a2ui || typeof a2ui !== "object") return null;
  const envelope = a2ui as Record<string, unknown>;
  return Array.isArray(envelope.a2ui_operations)
    ? (envelope.a2ui_operations as A2UIOp[])
    : null;
}

function isPresentResponse(data: unknown): data is PresentResponse {
  return (
    !!data &&
    typeof data === "object" &&
    "a2ui" in data &&
    typeof (data as Record<string, unknown>).expires_at === "string"
  );
}

function LinkUnavailable() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--bg)] px-6 text-[var(--ink)]">
      <div className="max-w-md rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface)] p-8 text-center shadow-[0_16px_50px_rgba(10,10,20,0.08)]">
        <p className="mono mb-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--lilac)]">
          Link unavailable
        </p>
        <h1 className="mb-3 text-[26px] font-semibold tracking-[-0.04em]">
          This link is no longer available
        </h1>
        <p className="text-[14px] leading-relaxed text-[var(--muted)]">
          The presentation link may have expired, been revoked, or never
          existed. Ask the agent to mint a fresh link.
        </p>
      </div>
    </main>
  );
}
