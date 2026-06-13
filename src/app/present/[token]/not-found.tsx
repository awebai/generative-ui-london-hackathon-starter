export default function LinkUnavailable() {
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
