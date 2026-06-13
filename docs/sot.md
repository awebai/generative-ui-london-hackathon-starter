# genui Source of Truth

`genui` is an **agent-first generative-UI app**: agents on an AWID team
work on shared team documents, and at any moment an agent can generate an
**A2UI artifact** and **present it to its human via a safe link** — a
rendered surface the human opens in a browser with no account, no login.
The agent is the user; the human is *summoned* by the agent to look at
something, exactly once per artifact.

It fuses two proven pieces:

- **atext's spine** (copied from `../atext`, billing excluded): a BYOT
  cert-auth relying party — agents authenticate with the request-bound v2
  team-auth envelope (`aw id request --team-auth`), every request scoped
  to the certificate's `team_id`, fail-closed. Team documents are
  append-only versioned UTF-8 text, every version attributed to the
  verified member.
- **the CopilotKit / AG-UI / A2UI generative-UI stack** (already wired in
  this repo): the agent emits declarative A2UI envelopes
  (`createSurface` / `updateComponents` / `updateDataModel`) against the
  21-component catalog; `@copilotkit/a2ui-renderer` turns them into live
  React.

## The core idea

An **A2UI artifact is a versioned document.** A2UI envelopes are
structured JSON — i.e. text — so the atext store holds them natively. The
flow:

1. An agent (cert-authenticated, working on team documents) generates an
   A2UI surface — from a document, a diff, a summary, an approval ask.
2. It stores the surface as a team-scoped, attributed artifact and **mints
   a presentation link**: an opaque, high-entropy, expiring capability
   token bound to one artifact version.
3. The agent hands the link to its human (the same primitive as a payment
   link: agent-minted, scoped, account-less).
4. The human opens `/present/<token>` in a browser; the Next.js frontend
   fetches the artifact and renders it with the CopilotKit A2UI renderer.
   No login — possession of the link is the capability.

## Two roles: user agents and the concierge

There is **one kind of principal — a cert-holding team member** — appearing
in two bodies:

- **User agents** — the team's working members (Claude Code, Codex, Pi),
  each with its own AWID team certificate. They do the team's work and
  decide *when* their human should be shown something.
- **The concierge** — a **per-team member whose body is the LangGraph
  agent** (this repo's `agent/`), specialized as a **web-research agent**:
  its tool is **LinkUp** (live web search), and it turns search results
  into cited A2UI surfaces that it presents via a safe link. It holds its
  **own AWID team-member identity and certificate**. User agents delegate
  research and presentation to it ("research X and show my human"). LinkUp
  lives here, in the deployed `agent/` — not in `server/`; the server has
  no search endpoint.

The concierge is not a privileged second class: it authenticates with a
team certificate like any member (`aw id request --team-auth`) and is
scoped to its team. **Each team runs its own concierge** so it acts within
that team's identity, data, and domain. The concierge is what keeps AG-UI,
the CopilotKit runtime, LangGraph, and LinkUp genuinely exercised; a user
agent may also compose and present a simple surface directly, since
`present_to_human` is just a cert-auth call any member can make.

This dissolves the "two kinds of agents" confusion: there is one principal
type, and the concierge is simply the member whose body is generative-UI
infrastructure rather than a coding harness.

**Identity and attribution.** team-auth has no on-behalf-of/delegation
primitive (confirmed with AWID): a request authenticates as exactly the
identity that signed it. So the concierge is a real, provisioned team
member — its own `.aw` identity, a controller-signed cert (alias
`concierge`), authenticating via `aw id request --team-auth` like every
other member (this is what the agent code already does). The authenticated
actor on a stored artifact is therefore the concierge; the **originating
user agent is recorded as artifact metadata** (`originating_agent`), not as
the cryptographic signer. A cleaner end-state — deferred past the
hackathon — is for the originating user agent to sign the store itself (the
concierge only composes), making origin attribution cryptographic. v1 uses
the concierge-as-member path. The concierge never reuses a user agent's
key and never signs as another identity. Demo setup requires provisioning
the concierge identity on the team once (`aw id create` → controller
`add-member` → `fetch-cert` → `team switch`).

## Authority model

Agents (user agents and the concierge alike) and humans authenticate by
two different paths — the one deliberate addition over atext's single path:

- **Agents** authenticate with AWID team certificates (atext's verifier,
  copied verbatim). They author documents and artifacts and mint links.
  Authoritative, team-scoped, fail-closed.
- **Humans** viewing a presentation authenticate by **possession of the
  capability token** only. A token is opaque (≥256 bits), bound to a
  single artifact version, expiring (default 24h), and read-only. Unknown
  or expired tokens return 404 (never reveal existence). The token grants
  read of exactly one rendered surface — nothing else, no team scope, no
  write.

genui never holds controller or namespace keys; AWID remains authoritative
for team keys and revocation. Stored text and A2UI envelopes are
server-readable (no E2E-encryption claim).

## Team isolation (hard invariant)

Artifacts and documents are strictly team-scoped. It is **impossible for
one team to read, list, present, or otherwise reach another team's
artifacts.** Enforced at every layer:

1. **Per-team concierge identity.** Each team has its own concierge — a
   distinct AWID member identity of that team, holding only that team's
   certificate. It authenticates with its team's cert, so its request
   Principal's `team_id` is its own team; it is structurally incapable of
   producing a valid envelope for another team (it does not hold another
   team's key). One concierge process must **never** hold multiple teams'
   member signing keys — per-team key isolation.
2. **Team stamped from the certificate, never the body.** On every write
   (documents, artifacts, present-link mint) the stored `team_id` comes
   from the verified Principal, never from request fields. A request
   cannot name another team to escape its scope.
3. **Cert-auth reads/lists scoped to the Principal's team.** Artifact and
   document get/list filter by `team_id = principal.team_id`. A member of
   team B requesting team A's `artifact_id` — even if guessed — gets 404,
   never the artifact.
4. **Present-link mint verifies ownership.** `POST /v1/present` MUST verify
   `artifact.team_id == principal.team_id` before minting; minting a link
   for an artifact the caller's team does not own fails 404. This is the
   critical new check — a present token can only ever be created by the
   artifact's own team.
5. **Public present leaks nothing.** `GET /present/{token}` resolves only
   the single artifact version the token was bound to (verified team-owned
   at mint), returns only `{a2ui, expires_at}`, and 404s on
   unknown/expired/revoked — no `team_id`, no `artifact_id`, no existence
   signal. The public link is the owner sharing one surface with its own
   human; it is account-less and team-less by design and exposes nothing
   else.

**Required negative tests (green before merge):** team B reading team A's
`artifact_id` → 404; team B's list never includes team A's artifacts; team
B's concierge minting a present link for team A's `artifact_id` → 404; a
write naming another team in the body lands in the caller's team (body
ignored); public `/present` returns only the bound artifact with no
team-identifying fields. These run as real cross-team e2e cases with two
distinct provisioned teams.

**Validated with AWID (Athena, 2026-06-13):** the per-team
concierge-as-member model, cert validation, and the isolation rules above
are confirmed sound — locked for v1. Hardening follow-ups she flagged,
**deferred past the hackathon (production, not demo)**:

- **Explicit attribution schema.** Record `authenticated_actor` (the
  signer = concierge) distinctly from `originating_agent` (metadata only;
  or `origin_signature = verified` if a signed origin intent is added
  later). Never let UI/copy claim the origin agent signed the server write.
- **Hosted vs BYOT provisioning.** The controller `aw id team add-member`
  path is correct for BYOT (customer holds the controller key). For hosted
  aweb-managed teams, provision the concierge member via the dashboard/API
  hosted flow instead.
- **Key custody.** One private signing key per team concierge; isolate key
  material per team (KMS / secret namespace / container boundary) in any
  multi-tenant process; never log private keys/certs/tokens; per-team
  revocation/rotation that doesn't touch other teams.
- **Real-deploy checklist (drop the demo shortcuts).** Verify namespace
  control via the DNS TXT flow; create namespace/team with real controller
  keys kept out of both the relying-party app and the concierge runtime
  (backed up, KMS/operator-held, with rotation/revocation); publish/sync
  team facts so verifiers resolve real AWID state; remove
  `--skip-dns-verify` and local-registry assumptions from prod config.
- **Present-link hardening.** Treat the capability token as bearer access:
  high entropy + expiry + revocation (have) **plus rate limiting**;
  responses expose no `team_id`/DIDs (have), but the artifact content
  itself may reveal customer data; keep 404 (not 403) for
  non-enumerability; cache negative/failed AWID states carefully and
  revalidate on a bounded TTL so revocation applies promptly.

## Components and processes

- **`server/`** — the atext spine as a standalone FastAPI relying party
  (Python 3.12, pgdbm, the copied `auth.py`). Owns documents, versions,
  A2UI artifacts, and presentation links. Cert-auth on the authoring side;
  capability-token on the public `/present` read side.
- **`agent/`** — the LangGraph/FastAPI AG-UI agent, **reshaped from the
  starter's pdf-analyst demo into the team's LinkUp web-research
  concierge** (pdf-analyst content removed). Its LinkUp tool searches the
  live web; it composes a cited A2UI surface and calls `present_to_human`
  to POST it to `server/`, mint a link, and return the safe URL.
- **`src/`** — the existing Next.js + CopilotKit frontend, plus a
  `/present/[token]` route that fetches an artifact by token and renders
  it with `@copilotkit/a2ui-renderer`. The existing chat/canvas demo stays
  intact (it satisfies the A2UI-firing requirement).

Three dev processes: Next.js (`:3000`), agent (`:8123`), server
(`:8200`). A Makefile target and the compose file run all three.

## API shape (server/)

Agent-facing (team-cert auth, v2 envelope, scoped to the cert's team):
- `POST /v1/documents`, `GET /v1/documents`, `GET /v1/documents/{slug}`,
  `GET|POST /v1/documents/{slug}/versions` — copied from atext.
- `POST /v1/artifacts` — store an A2UI surface (the envelope JSON) as a
  team-scoped, attributed artifact; returns its id + version.
- `GET /v1/artifacts`, `GET /v1/artifacts/{id}` — list/read (cert-auth).
- `POST /v1/present` — mint a presentation link for an artifact version;
  body `{artifact_id, version?, ttl_seconds?}`; returns
  `{token, url, expires_at}`.

Public (capability-token, no cert):
- `GET /present/{token}` — returns the A2UI envelope JSON for the bound
  artifact version if the token is valid and unexpired; else 404.

Ops: `/live`, `/ready`, `/health`.

## Data model (server/)

Reuse atext's Team, Document, Document version verbatim. New:

- **Artifact** — `artifact_id` (uuid), `team_id`, optional `slug`,
  `kind` (`a2ui`), creator identity fields (did_key/did_aw/address/alias,
  certificate_id), timestamps. Append-only **artifact versions** hold the
  envelope JSON (`createSurface`/`updateComponents`/`updateDataModel` ops),
  monotonic version number, creator identity.
- **Presentation link** — `token` (opaque, unique), `artifact_id`,
  `version_number`, `team_id`, `created_by_did_key`, `expires_at`,
  `revoked_at` (nullable), `created_at`. Lookups are by token; expired or
  revoked → 404.

## Excluded from atext (no payment)

No subscription table, no caps, no `GET /v1/billing`, no Stripe, no 402.
Drop `migrations/002_subscriptions.sql`, `test_billing_caps.py`, and all
billing routes/models/config when copying.

## Hackathon requirements (must all hold)

- **CopilotKit** is used (required) — the runtime + `@copilotkit/a2ui-renderer`
  render both the live chat canvas and the `/present` view.
- **A2UI is firing** — real `createSurface`/`updateComponents` envelopes
  fire and are renderable; keep 1–2 sample envelopes for submission.
- **AG-UI** carries envelopes agent→frontend (existing wiring).
- Submission copy names **Google DeepMind, CopilotKit, A2A Net, Linkup,
  Redis**.
- Deliverables: public repo, demo URL (Vercel), 30s video, one-paragraph
  pitch, envelope sample. Backup: `OFFLINE=1` canned surface.
- A2A interop (Seam #6) is optional/stretch.

## Validation

- Server unit/e2e reuses atext's no-mocks harness: local awid-service +
  postgres, real certs via `aw id`, real signed requests. Cover: artifact
  CRUD under cert-auth, team scoping (no cross-team artifact read),
  link mint → token fetch → expiry → revoke, fail-closed.
- Capability-token path tested for the security invariants: opaque,
  single-version binding, expiry, 404 on unknown/expired, no team leakage.
- A frontend smoke: `/present/<token>` renders a stored surface.
- The existing CopilotKit demo keeps working (`pnpm dev`, the canned
  prompt sequence).

## Build process

Build in this repo (`awebai/generative-ui-london-hackathon-starter`,
locally `~/prj/awebai/genui`), branches off `main`, independent review
before merge, coordinator verifies on merged main. Frozen starter versions
stay pinned (see `FROZEN.md`); do not bump.

## Non-goals (v1)

- No payment of any kind.
- No live human-steers-the-agent streaming in v1 — base case is
  store-artifact → render-by-link. Live AG-UI relay to `/present` is a
  later upgrade on the same spine.
- No human accounts, OAuth, sessions, or write access from the `/present`
  side.
