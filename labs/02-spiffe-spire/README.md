# Lab 02 — SPIFFE/SPIRE workload identity (experimental)

**Status:** Compose scaffolding and configuration committed; not yet end-to-end verified. This lab intentionally does not replace Keycloak in Lab 01. SPIRE is not a JWT token exchange service for the existing gateway without additional integration.

## Goal

Understand SPIFFE trust domains, SPIRE server/agent, node attestation, workload attestation and short-lived SVID issuance. Distinguish node registration from workload registration.

**Security warning:** This draft uses a join-token bootstrap and a host PID namespace to simplify local experimentation. It is not a production deployment pattern. Do not run on a shared or untrusted Docker host.

## Step 1 — Start server

**Bash (Linux/macOS)**

```bash
docker compose -f compose.identity.yaml up -d spire-server
docker compose -f compose.identity.yaml ps -a
docker compose -f compose.identity.yaml logs --tail=50 spire-server
```

**PowerShell (Windows)**

```powershell
docker compose -f compose.identity.yaml up -d spire-server
docker compose -f compose.identity.yaml ps -a
docker compose -f compose.identity.yaml logs --tail=50 spire-server
```

## Step 2 — Generate node join token

**Bash**

```bash
docker compose -f compose.identity.yaml exec spire-server /opt/spire/bin/spire-server token generate -spiffeID spiffe://lab.local/spire/agent/demo
```

**PowerShell**

```powershell
docker compose -f compose.identity.yaml exec spire-server /opt/spire/bin/spire-server token generate -spiffeID spiffe://lab.local/spire/agent/demo
```

Copy only the returned token value to your local environment. It is a bootstrap secret.

**Bash**

```bash
export SPIRE_JOIN_TOKEN='PASTE_JOIN_TOKEN_HERE'
docker compose -f compose.identity.yaml up -d spire-agent
docker compose -f compose.identity.yaml logs --tail=50 spire-agent
```

**PowerShell**

```powershell
$env:SPIRE_JOIN_TOKEN = 'PASTE_JOIN_TOKEN_HERE'
docker compose -f compose.identity.yaml up -d spire-agent
docker compose -f compose.identity.yaml logs --tail=50 spire-agent
```

## Step 3 — Inspect registered nodes

**Bash**

```bash
docker compose -f compose.identity.yaml exec spire-server /opt/spire/bin/spire-server agent list
```

**PowerShell**

```powershell
docker compose -f compose.identity.yaml exec spire-server /opt/spire/bin/spire-server agent list
```

Expected: a registered agent node. This **does not yet prove** a workload obtained an SVID.

## Step 4 — Workload registration and SVID issuance

**Pending integration test.** The next iteration will register a constrained workload selector, mount the SPIRE Workload API socket into a test workload, retrieve an SVID, and verify that an unauthorized workload cannot retrieve it. We will not claim the SPIFFE workload identity control is validated until these positive and negative tests run.

## Step 5 — Cleanup

**Bash**

```bash
docker compose -f compose.identity.yaml down -v
unset SPIRE_JOIN_TOKEN
```

**PowerShell**

```powershell
docker compose -f compose.identity.yaml down -v
Remove-Item Env:SPIRE_JOIN_TOKEN -ErrorAction SilentlyContinue
```

## Important limitations

- Windows/macOS Docker Desktop uses a Linux VM; `pid: host` is scoped to that VM, not the native Windows/macOS host.
- The draft is **not yet a deployable end-to-end SVID exercise**; SPIRE server/agent configuration and image behavior need smoke testing.
- A join token establishes node enrollment, not workload identity.
- No SPIFFE-to-OpenBao trust integration is claimed.
