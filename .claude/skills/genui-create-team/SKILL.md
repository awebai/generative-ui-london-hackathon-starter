---
name: "genui:create-team"
description: Use when someone asks to create a team, set up a team, onboard my team to atext, get my agents on atext, join a team, invite a teammate, add an agent to atext, create an AWID team for genui/atext, or prepare agents to use atext.ai. Covers the verified hosted aweb on-ramp first, with BYOT/DNS as advanced.
version: 1.0.0
---

# genui:create-team

Use this when a new team wants to use atext/genui.

Goal: each agent ends with an AWID team certificate in its workspace. Then the
agent can call atext with `aw id request --team-auth`.

## Fast path: hosted aweb team

This is the simplest path for a demo or a new team. It resolves in the public
AWID registry, so `https://api.atext.ai` can verify it.

### 1. Install `aw`

```bash
npm install -g @awebai/aw
aw --version
```

### 2. Create your identity + first team workspace

Run in the first agent's workspace:

```bash
aw init --username <your-aweb-username> --alias alpha
```

Verify:

```bash
aw workspace status
aw id cert show
```

### 3. Invite a teammate / second agent

From the first workspace:

```bash
aw team invite
```

Send the printed token to the teammate. In the teammate's clean workspace:

```bash
aw team join <invite-token> --alias beta
aw init
```

If `aw team join` prints different next steps, follow those exact steps.

Verify in the teammate workspace:

```bash
aw workspace status
aw id cert show
```

### 4. Point agents at atext

In any team-member workspace:

```bash
export SERVER_ORIGIN=https://api.atext.ai
```

Now use:

- `genui:present-to-human` — create/append docs, store A2UI, mint/open a `/present` link.
- `genui:compose-a2ui` — compose a valid renderer-safe A2UI surface.

## Advanced: BYOT / DNS-backed team

Use this only when the organization must control its own DNS namespace and team
controller keys.

Controller machine:

```bash
aw id namespace prepare-controller --domain <domain>
# publish the exact _awid.<domain> TXT record printed by the command
aw id namespace check-txt --domain <domain>
aw id team create --namespace <domain> --name <team> --display-name "<display name>"
```

Back up `~/.awid`; it contains controller private keys.

Each member creates an identity in its own workspace:

```bash
aw id create --domain <domain> --name <alias>
```

Controller signs that member into the team using the member's printed DID values:

```bash
aw id team add-member \
  --team <team> \
  --namespace <domain> \
  --did <member_did_key> \
  --alias <alias> \
  --global \
  --did-aw <member_did_aw>
```

Member installs and activates the certificate:

```bash
aw id team fetch-cert --namespace <domain> --team <team> --cert-id <cert-id>
aw id team switch <team>:<domain>
```

Then:

```bash
export SERVER_ORIGIN=https://api.atext.ai
```

Never copy private signing keys or controller keys between machines.
