# Lab 03 — OpenBao secrets and revocation (development lab)

**Status:** Initial runnable exercise candidate; not yet execution-verified. This is an **independent OpenBao secrets lab**, not SPIFFE authentication. It uses a local development root token for setup only.

## Goals

Demonstrate a policy-scoped token that can read only an allowed synthetic secret, is denied access to another path, and stops working after revocation.

## Step 1 — Start OpenBao

**Bash**

```bash
docker compose -f compose.secrets.yaml up -d
docker compose -f compose.secrets.yaml ps
```

**PowerShell**

```powershell
docker compose -f compose.secrets.yaml up -d
docker compose -f compose.secrets.yaml ps
```

## Step 2 — Create a KV store, synthetic secrets and read-only policy

**Bash**

```bash
docker compose -f compose.secrets.yaml exec -e BAO_TOKEN=lab-root-token openbao bao secrets enable -path=lab -version=2 kv
docker compose -f compose.secrets.yaml exec -e BAO_TOKEN=lab-root-token openbao bao kv put lab/allowed demo_key=synthetic-only
docker compose -f compose.secrets.yaml exec -e BAO_TOKEN=lab-root-token openbao bao kv put lab/restricted demo_key=do-not-read
docker compose -f compose.secrets.yaml exec -T -e BAO_TOKEN=lab-root-token openbao bao policy write agent-read - <<'EOF'
path "lab/data/allowed" {
  capabilities = ["read"]
}
EOF
```

**PowerShell**

```powershell
docker compose -f compose.secrets.yaml exec -e BAO_TOKEN=lab-root-token openbao bao secrets enable -path=lab -version=2 kv
docker compose -f compose.secrets.yaml exec -e BAO_TOKEN=lab-root-token openbao bao kv put lab/allowed demo_key=synthetic-only
docker compose -f compose.secrets.yaml exec -e BAO_TOKEN=lab-root-token openbao bao kv put lab/restricted demo_key=do-not-read
@'
path "lab/data/allowed" {
  capabilities = ["read"]
}
'@ | docker compose -f compose.secrets.yaml exec -T -e BAO_TOKEN=lab-root-token openbao bao policy write agent-read -
```

## Step 3 — Issue a scoped, short-lived token

**Bash**

```bash
docker compose -f compose.secrets.yaml exec -e BAO_TOKEN=lab-root-token openbao bao token create -policy=agent-read -ttl=10m -renewable=false -format=json
```

**PowerShell**

```powershell
docker compose -f compose.secrets.yaml exec -e BAO_TOKEN=lab-root-token openbao bao token create -policy=agent-read -ttl=10m -renewable=false -format=json
```

Copy the `auth.client_token` value to a local variable; never commit or publish it.

**Bash**

```bash
export AGENT_BAO_TOKEN='PASTE_SCOPED_TOKEN_HERE'
```

**PowerShell**

```powershell
$env:AGENT_BAO_TOKEN = 'PASTE_SCOPED_TOKEN_HERE'
```

## Step 4 — Allowed read and denied read

**Bash**

```bash
curl -i -H "X-Vault-Token: $AGENT_BAO_TOKEN" http://localhost:8200/v1/lab/data/allowed
curl -i -H "X-Vault-Token: $AGENT_BAO_TOKEN" http://localhost:8200/v1/lab/data/restricted
```

**PowerShell**

```powershell
curl.exe -i -H "X-Vault-Token: $env:AGENT_BAO_TOKEN" http://localhost:8200/v1/lab/data/allowed
curl.exe -i -H "X-Vault-Token: $env:AGENT_BAO_TOKEN" http://localhost:8200/v1/lab/data/restricted
```

Expected: allowed path **200**, restricted path **403**.

## Step 5 — Revoke and prove access denial

**Bash**

```bash
docker compose -f compose.secrets.yaml exec -e BAO_TOKEN=lab-root-token openbao bao token revoke "$AGENT_BAO_TOKEN"
curl -i -H "X-Vault-Token: $AGENT_BAO_TOKEN" http://localhost:8200/v1/lab/data/allowed
```

**PowerShell**

```powershell
docker compose -f compose.secrets.yaml exec -e BAO_TOKEN=lab-root-token openbao bao token revoke $env:AGENT_BAO_TOKEN
curl.exe -i -H "X-Vault-Token: $env:AGENT_BAO_TOKEN" http://localhost:8200/v1/lab/data/allowed
```

Expected: revoked token denied (**403** or equivalent auth failure). Confirm via response and logs.

## Step 6 — Cleanup

**Bash**

```bash
docker compose -f compose.secrets.yaml down -v
unset AGENT_BAO_TOKEN
```

**PowerShell**

```powershell
docker compose -f compose.secrets.yaml down -v
Remove-Item Env:AGENT_BAO_TOKEN -ErrorAction SilentlyContinue
```

## Security limitations

- Dev server is ephemeral, unsealed, and uses a fixed root token. **Never use in production.**
- The lab tests OpenBao authorization and token revocation, **not** workload-bound credential issuance.
- The SPIFFE/SPIRE → OpenBao authentication and dynamic credentials flow is a later integration milestone.
