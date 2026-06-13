import { notFound } from "next/navigation";
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
    notFound();
  }

  return (
    <main className="present-shell">
      <header className="present-header">
        <p className="present-eyebrow mono">Presented document</p>
        <h1 className="present-title mono">shared A2UI surface</h1>
        <p className="present-copy">
          This link was minted by a verified team agent. No browser login is
          required; possession of the token grants read-only access to this one
          A2UI-formatted document.
        </p>
      </header>
      <section className="a2ui-surface present-card">
        <PresentSurface operations={operations} />
      </section>
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
