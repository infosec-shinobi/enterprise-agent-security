# Lab 01: Registry, identity, authorization and suspension

This is a **local-only educational demo**, not a production-ready identity or authorization system. It uses a fixed demonstration Keycloak client secret and administrative key. Do not expose ports to a network or reuse these credentials.

## Start

From the repository root:

```bash
docker compose up --build -d
docker compose ps
```

Wait for Keycloak to initialize (first boot may take a minute).

## Windows PowerShell 7+

Run these commands in PowerShell. These use native PowerShell HTTP commands, not Bash `curl` syntax.

```powershell
$response = Invoke-RestMethod -Uri 'http://localhost:8081/realms/agent-lab/protocol/openid-connect/token' -Method POST -Body @{ grant_type='client_credentials'; client_id='agent-demo'; client_secret='local-demo-secret' }
$TOKEN = $response.access_token
$TOKEN.Length
```

Then test the lifecycle (HTTP 403 is an expected result for denied actions):

```powershell
$headers = @{ Authorization = "Bearer $TOKEN" }
$admin = @{ 'X-Lab-Admin-Key' = 'local-demo-admin-key' }
Invoke-WebRequest -Uri 'http://localhost:8001/tools/records/123' -Headers $headers -SkipHttpErrorCheck | Select-Object StatusCode,Content
Invoke-RestMethod -Method POST -Uri 'http://localhost:8000/agents/agent-demo?owner=lab-owner' -Headers $admin
Invoke-WebRequest -Uri 'http://localhost:8001/tools/records/123' -Headers $headers -SkipHttpErrorCheck | Select-Object StatusCode,Content
Invoke-RestMethod -Method POST -Uri 'http://localhost:8000/agents/agent-demo/state/active' -Headers $admin
Invoke-WebRequest -Uri 'http://localhost:8001/tools/records/123' -Headers $headers -SkipHttpErrorCheck | Select-Object StatusCode,Content
Invoke-WebRequest -Method DELETE -Uri 'http://localhost:8001/tools/records/123' -Headers $headers -SkipHttpErrorCheck | Select-Object StatusCode,Content
Invoke-RestMethod -Method POST -Uri 'http://localhost:8000/agents/agent-demo/state/suspended' -Headers $admin
Invoke-WebRequest -Uri 'http://localhost:8001/tools/records/123' -Headers $headers -SkipHttpErrorCheck | Select-Object StatusCode,Content
docker compose logs gateway
```

Expected gateway HTTP statuses: **403, 403, 200, 403, 403**. Re-running registration after a prior attempt returns 409; use `docker compose down -v` to reset. PowerShell 5.1 lacks `-SkipHttpErrorCheck`; use PowerShell 7+ or catch HTTP errors explicitly.

## Obtain a client credentials token (Bash)

```bash
TOKEN=$(curl -fsS -X POST http://localhost:8081/realms/agent-lab/protocol/openid-connect/token -d grant_type=client_credentials -d client_id=agent-demo -d client_secret=local-demo-secret | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
```

The JWT proves client authentication. It is **not SPIFFE-attested workload identity**. The gateway verifies signature, issuer, audience and expiration against Keycloak's JWKS.

## Validate the lifecycle

```bash
# Unregistered agent: 403
curl -i -H "Authorization: Bearer $TOKEN" http://localhost:8001/tools/records/123

# Register, but do not approve: still 403
curl -X POST -H "X-Lab-Admin-Key: local-demo-admin-key" 'http://localhost:8000/agents/agent-demo?owner=lab-owner'
curl -i -H "Authorization: Bearer $TOKEN" http://localhost:8001/tools/records/123

# Simulated approval activates the agent
curl -X POST -H "X-Lab-Admin-Key: local-demo-admin-key" http://localhost:8000/agents/agent-demo/state/active

# Read: 200; delete: 403
curl -i -H "Authorization: Bearer $TOKEN" http://localhost:8001/tools/records/123
curl -i -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:8001/tools/records/123

# Suspend: the same previously issued token must now receive 403
curl -X POST -H "X-Lab-Admin-Key: local-demo-admin-key" http://localhost:8000/agents/agent-demo/state/suspended
curl -i -H "Authorization: Bearer $TOKEN" http://localhost:8001/tools/records/123

# Inspect gateway audit logs
docker compose logs gateway
```

## Security boundaries and limitations

- Registry is an inventory and lifecycle control-plane component.
- Keycloak authenticates the demonstration client; SPIRE attestation is **not implemented**.
- OPA is a policy decision point; the tool gateway enforces its decision.
- The protected resource is synthetic and returned by the gateway itself; a separate downstream API is **not yet implemented**.
- Registry lookup is internal-network-only and unauthenticated; later milestones must add service-to-service authentication.
- Audit records currently go to container logs; OpenTelemetry/Loki/Tempo are **not yet wired**.
- Admin authentication uses a static demo key; no approval separation of duties exists.
- Policy is evaluated on each request; availability of registry/OPA is required and failures deny access.
- Keycloak is bound to localhost; this is a single-host local development configuration.

## Reset

```bash
docker compose down -v
```

This deletes lab registry data.
