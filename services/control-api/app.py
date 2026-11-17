import os, sqlite3, json, time, uuid, logging
from fastapi import FastAPI, HTTPException, Header, Request
import httpx
import jwt
from jwt import PyJWKClient

app = FastAPI(title="Agent Security Control Plane Demo")
logging.basicConfig(level=logging.INFO)
MODE = os.getenv("MODE", "registry")
DB = os.getenv("DB_PATH", "/data/registry.db")
ADMIN = os.getenv("ADMIN_KEY", "local-demo-admin-key")

def connection():
    db = sqlite3.connect(DB)
    db.execute("CREATE TABLE IF NOT EXISTS agents (id TEXT PRIMARY KEY, owner TEXT NOT NULL, lifecycle TEXT NOT NULL)")
    db.commit()
    return db

def require_admin(key):
    if not key or key != ADMIN:
        raise HTTPException(403, "Invalid lab admin key")

@app.get("/health")
def health():
    return {"ok": True, "mode": MODE}

@app.post("/agents/{agent_id}")
def register(agent_id: str, owner: str, x_lab_admin_key: str | None = Header(None)):
    if MODE != "registry": raise HTTPException(404)
    require_admin(x_lab_admin_key)
    if agent_id != "agent-demo": raise HTTPException(400, "Demo supports agent-demo only")
    with connection() as db:
        try: db.execute("INSERT INTO agents VALUES (?,?,?)", (agent_id, owner, "draft"))
        except sqlite3.IntegrityError: raise HTTPException(409, "Already registered")
    return {"agent_id": agent_id, "lifecycle": "draft"}

@app.post("/agents/{agent_id}/state/{state}")
def transition(agent_id: str, state: str, x_lab_admin_key: str | None = Header(None)):
    if MODE != "registry": raise HTTPException(404)
    require_admin(x_lab_admin_key)
    if state not in ("active", "suspended", "retired"): raise HTTPException(400, "Invalid state")
    with connection() as db:
        row = db.execute("SELECT lifecycle FROM agents WHERE id=?", (agent_id,)).fetchone()
        if not row: raise HTTPException(404, "Not registered")
        current = row[0]
        valid = {"draft": ["active"], "active": ["suspended", "retired"], "suspended": ["active", "retired"], "retired": []}
        if state not in valid[current]: raise HTTPException(409, "Invalid transition")
        db.execute("UPDATE agents SET lifecycle=? WHERE id=?", (state, agent_id))
    return {"agent_id": agent_id, "lifecycle": state}

@app.get("/internal/agents/{agent_id}")
def lookup(agent_id: str):
    if MODE != "registry": raise HTTPException(404)
    with connection() as db:
        row = db.execute("SELECT owner,lifecycle FROM agents WHERE id=?", (agent_id,)).fetchone()
    if not row: raise HTTPException(404, "Not registered")
    return {"agent_id": agent_id, "owner": row[0], "lifecycle": row[1]}

@app.api_route("/tools/records/{record_id}", methods=["GET", "DELETE"])
async def tool(record_id: str, request: Request, authorization: str | None = Header(None)):
    if MODE != "gateway": raise HTTPException(404)
    trace_id = str(uuid.uuid4())
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401, "Missing bearer token")
    token = authorization[7:]
    try:
        jwks = PyJWKClient(os.environ["JWKS_URL"])
        signing_key = jwks.get_signing_key_from_jwt(token)
        claims = jwt.decode(token, signing_key.key, algorithms=["RS256"], audience=os.environ["EXPECTED_AUDIENCE"], issuer=os.environ["EXPECTED_ISSUER"])
        agent_id = claims.get("azp")
        if not agent_id: raise ValueError("No client identity")
    except Exception as exc:
        logging.warning("authentication_failed trace_id=%s reason=%s", trace_id, type(exc).__name__)
        raise HTTPException(401, "Invalid token")
    action = "records:read" if request.method == "GET" else "records:delete"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f'{os.environ["REGISTRY_URL"]}/internal/agents/{agent_id}')
            registered = r.status_code == 200
            lifecycle = r.json()["lifecycle"] if registered else "unknown"
            decision = await client.post(os.environ["OPA_URL"], json={"input":{"identity_valid":True,"registered":registered,"lifecycle":lifecycle,"action":action,"resource":"synthetic-customer-records"}})
            decision.raise_for_status()
            allowed = decision.json().get("result") is True
    except Exception as exc:
        logging.error("policy_dependency_failure trace_id=%s error=%s",trace_id,type(exc).__name__)
        raise HTTPException(503, "Authorization unavailable; denied")
    logging.info("audit=%s",json.dumps({"trace_id":trace_id,"agent_id":agent_id,"action":action,"record_id":record_id,"lifecycle":lifecycle,"allowed":allowed,"timestamp":int(time.time())}))
    if not allowed: raise HTTPException(403, "Denied by policy")
    return {"record_id":record_id,"customer":"Synthetic Customer","classification":"DEMO","trace_id":trace_id}
