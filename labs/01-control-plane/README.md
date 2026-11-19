# Lab 01 — Registry, identity, authorization and suspension

**Platforms:** Linux/macOS (Bash) and Windows (PowerShell 5.1 or 7+). Each step has both command variants; run **only one** variant per step. Docker Compose commands are the same on both platforms.

**Safety:** Local educational demo with fixed test secrets and synthetic records. Do not expose it publicly or reuse the credentials. The source has not yet been verified end-to-end on all platforms.

## Prerequisites

Docker Engine/Desktop with Compose v2; Bash + curl + Python 3 on Linux/macOS, or Windows PowerShell 5.1/PowerShell 7 with `curl.exe` and `Invoke-RestMethod`. Run commands from the repository root.

### Step 1 — Start the environment

**Bash (Linux/macOS)**

```bash
docker compose up --build -d
docker compose ps -a
```

**PowerShell (Windows)**

```powershell
docker compose up --build -d
docker compose ps -a
```

Wait for Keycloak to become healthy. All four services (`keycloak`, `registry`, `gateway`, `opa`) must be running. A missing OPA container means authorization requests will fail closed with 503. Inspect `docker compose logs opa` if needed.

### Step 2 — Obtain a Keycloak client credentials token

**Bash (Linux/macOS)**

```bash
TOKEN=$(curl -fsS -X POST 'http://localhost:8081/realms/agent-lab/protocol/openid-connect/token' \
  -d grant_type=client_credentials \
  -d client_id=agent-demo \
  -d client_secret=local-demo-secret | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
echo "Token length: ${#TOKEN}"
```

**PowerShell (Windows 5.1 / 7+)**

```powershell
$response = Invoke-RestMethod -Uri 'http://localhost:8081/realms/agent-lab/protocol/openid-connect/token' -Method POST -Body @{
  grant_type = 'client_credentials'
  client_id = 'agent-demo'
  client_secret = 'local-demo-secret'
}
$TOKEN = $response.access_token
Write-Host "Token length: $($TOKEN.Length)"
```

Expected: nonzero token length. Do not paste the JWT into issues or public logs. This is a Keycloak client credential, **not** a SPIFFE-attested identity.

### Step 3 — Test an unregistered agent

**Bash**

```bash
curl -i -H "Authorization: Bearer $TOKEN" 'http://localhost:8001/tools/records/123'
```

**PowerShell**

```powershell
curl.exe -i -H "Authorization: Bearer $TOKEN" 'http://localhost:8001/tools/records/123'
```

Expected gateway HTTP **403** (unregistered). HTTP 503 indicates a registry or OPA dependency problem, not a passing policy test. A 401 indicates token verification failed.

### Step 4 — Register the agent (draft state)

**Bash**

```bash
curl -i -X POST -H 'X-Lab-Admin-Key: local-demo-admin-key' 'http://localhost:8000/agents/agent-demo?owner=lab-owner'
curl -i -H "Authorization: Bearer $TOKEN" 'http://localhost:8001/tools/records/123'
```

**PowerShell**

```powershell
curl.exe -i -X POST -H 'X-Lab-Admin-Key: local-demo-admin-key' 'http://localhost:8000/agents/agent-demo?owner=lab-owner'
curl.exe -i -H "Authorization: Bearer $TOKEN" 'http://localhost:8001/tools/records/123'
```

Expected: registration HTTP **200**, state `draft`; tool request HTTP **403**. If registration returns 409, the agent already exists from a previous run.

### Step 5 — Activate (simplified approval simulation)

**Bash**

```bash
curl -i -X POST -H 'X-Lab-Admin-Key: local-demo-admin-key' 'http://localhost:8000/agents/agent-demo/state/active'
```

**PowerShell**

```powershell
curl.exe -i -X POST -H 'X-Lab-Admin-Key: local-demo-admin-key' 'http://localhost:8000/agents/agent-demo/state/active'
```

Expected: HTTP **200**, state `active`. This is **not** a real multi-party approval workflow.

### Step 6 — Allow read; deny delete

**Bash**

```bash
curl -i -H "Authorization: Bearer $TOKEN" 'http://localhost:8001/tools/records/123'
curl -i -X DELETE -H "Authorization: Bearer $TOKEN" 'http://localhost:8001/tools/records/123'
```

**PowerShell**

```powershell
curl.exe -i -H "Authorization: Bearer $TOKEN" 'http://localhost:8001/tools/records/123'
curl.exe -i -X DELETE -H "Authorization: Bearer $TOKEN" 'http://localhost:8001/tools/records/123'
```

Expected: read HTTP **200**, delete HTTP **403**. If token expired, repeat Step 2.

### Step 7 — Suspend the agent and retry with the same token

**Bash**

```bash
curl -i -X POST -H 'X-Lab-Admin-Key: local-demo-admin-key' 'http://localhost:8000/agents/agent-demo/state/suspended'
curl -i -H "Authorization: Bearer $TOKEN" 'http://localhost:8001/tools/records/123'
```

**PowerShell**

```powershell
curl.exe -i -X POST -H 'X-Lab-Admin-Key: local-demo-admin-key' 'http://localhost:8000/agents/agent-demo/state/suspended'
curl.exe -i -H "Authorization: Bearer $TOKEN" 'http://localhost:8001/tools/records/123'
```

Expected: suspension HTTP **200**, subsequent read HTTP **403**. The test demonstrates authorization denial for a suspended registry state; it does **not** revoke the token.

### Step 8 — Inspect audit and dependency logs

**Bash**

```bash
docker compose logs --tail=100 gateway
docker compose logs --tail=100 opa registry
```

**PowerShell**

```powershell
docker compose logs --tail=100 gateway
docker compose logs --tail=100 opa registry
```

Expected: gateway `audit=` records for successfully evaluated requests. Authentication failures and dependency failures may use different log records.

### Step 9 — Reset (deletes all lab registry data)

**Bash**

```bash
docker compose down -v
```

**PowerShell**

```powershell
docker compose down -v
```

**Expected gateway status sequence:** 403 → 403 → 200 → 403 → 403.

## Troubleshooting (both shells)

| Symptom | Likely cause | Command |
| --- | --- | --- |
| Gateway 503 | OPA or registry unavailable / error | `docker compose ps -a` and `docker compose logs opa gateway registry` |
| OPA exits with `rego_parse_error` | Outdated Rego policy file | `git pull origin main` then `docker compose up -d opa` |
| Gateway 401 | JWT expired or issuer/audience/signature mismatch | Refresh token (Step 2); check gateway logs |
| Registration 409 | Agent already exists | Continue from current state or reset |
| Port conflict | Another service using 8000, 8001 or 8081 | Stop conflicting service; inspect Compose ports |

## Architecture and security limitations

- **Control plane:** registry, Keycloak and OPA policy decision point.
- **Data plane:** tool gateway as policy enforcement point; synthetic record response.
- Registry lookup is unauthenticated inside the Compose network; later milestones must secure service-to-service calls.
- OpenBao, SPIRE/SPIFFE, OpenTelemetry, Loki and Tempo are **not implemented in this lab yet**.
- The lab uses a static admin key and fixed client secret; not suitable for production.
- OPA and registry failures deny protected operations, but a 503 is **not** equivalent to a passing expected-deny test.
- The tool gateway currently returns synthetic records itself; a separate enterprise API is a later milestone.
