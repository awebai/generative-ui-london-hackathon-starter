export default function LinkUnavailable() {
  return (
    <main className="present-shell">
      <section className="present-card" style={{ maxWidth: "32rem", margin: "10vh auto 0" }}>
        <p className="present-eyebrow mono">Link unavailable</p>
        <h1 className="present-title mono">this link is no longer available</h1>
        <p className="present-copy">
          The presentation token may have expired, been revoked, or never
          existed. Ask your agent to mint a fresh document link.
        </p>
      </section>
    </main>
  );
}
