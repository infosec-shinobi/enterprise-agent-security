"""Bounded, read-only host-side service observations."""
import asyncio
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
import httpx
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

@dataclass(frozen=True)
class Service:
    id: str
    name: str
    role: str
    url: str | None = None

SERVICES = (
    Service("keycloak", "Keycloak", "Identity provider", "http://127.0.0.1:8081/realms/agent-lab/.well-known/openid-configuration"),
    Service("registry", "Agent registry", "Lifecycle management", "http://127.0.0.1:8000/health"),
    Service("opa", "OPA", "Policy decision point"),
    Service("gateway", "Tool gateway", "Enforcement point", "http://127.0.0.1:8001/health"),
    Service("openbao", "OpenBao", "Credential management", "http://127.0.0.1:8200/v1/sys/health"),
    Service("spire-server", "SPIRE server", "Workload identity authority"),
    Service("spire-agent", "SPIRE agent", "Workload attestation"),
)
BY_ID = {s.id: s for s in SERVICES}
DEADLINE = 3.0
MAX_BODY = 65536
router = APIRouter(prefix="/api/v1/services", tags=["services"])

class Observation(BaseModel):
    id: str
    name: str
    role: str
    endpoint: str | None
    status: Literal["available", "unavailable", "unknown"]
    reason: str
    checked_at: datetime
    duration_ms: int | None
    http_status: int | None
    control_effectiveness: Literal["not_assessed"] = "not_assessed"

class Snapshot(BaseModel):
    services: list[Observation]

def matches(service, data):
    if not isinstance(data, dict):
        return False
    if service.id in ("registry", "gateway"):
        return data.get("ok") is True and data.get("mode") == service.id
    if service.id == "keycloak":
        return data.get("issuer") in (
            "http://127.0.0.1:8081/realms/agent-lab",
            "http://localhost:8081/realms/agent-lab",
        ) and isinstance(data.get("token_endpoint"), str)
    if service.id == "openbao":
        return data.get("initialized") is True and data.get("sealed") is False and data.get("standby") is False
    return False

async def probe(service: Service, client: httpx.AsyncClient) -> Observation:
    start = time.monotonic()
    code = None
    def result(status, reason):
        return Observation(id=service.id, name=service.name, role=service.role,
            endpoint=service.url, status=status, reason=reason,
            checked_at=datetime.now(timezone.utc),
            duration_ms=int((time.monotonic()-start)*1000) if service.url else None,
            http_status=code)
    if not service.url:
        return result("unknown", "No host-accessible probe configured")
    async def request():
        nonlocal code
        async with client.stream("GET", service.url, headers={"Accept-Encoding":"identity"}) as response:
            code = response.status_code
            if code != 200:
                return result("unavailable", "Unexpected HTTP status")
            if response.headers.get("content-encoding", "identity").lower() != "identity":
                return result("unknown", "Unsupported response encoding")
            raw = bytearray()
            async for chunk in response.aiter_raw(chunk_size=4096):
                if len(raw)+len(chunk)>MAX_BODY:
                    return result("unknown", "Response size limit exceeded")
                raw.extend(chunk)
            try:
                data = json.loads(raw)
            except (ValueError, RecursionError):
                return result("unknown", "Invalid JSON response")
            if not matches(service, data):
                return result("unknown", "Unexpected service response")
            return result("available", "Expected probe response received")
    try:
        return await asyncio.wait_for(request(), timeout=DEADLINE)
    except (asyncio.TimeoutError, httpx.TimeoutException):
        return result("unavailable", "Probe timed out")
    except httpx.RequestError:
        return result("unavailable", "Probe connection or protocol failed")

async def observe(ids, transport=None):
    # Only canonical server-owned IDs are resolved. No caller-supplied URLs.
    async with httpx.AsyncClient(timeout=2.0, follow_redirects=False, trust_env=False,
                                 transport=transport, limits=httpx.Limits(max_connections=4)) as client:
        return Snapshot(services=await asyncio.gather(*(probe(BY_ID[i], client) for i in ids)))

# Limit overlapping snapshots per local API process.
gate = asyncio.Lock()

async def collect(ids, response):
    if gate.locked():
        raise HTTPException(429, "Health probe already in progress")
    async with gate:
        response.headers["Cache-Control"] = "no-store"
        return await observe(ids)

@router.get("", response_model=Snapshot)
async def list_services(response: Response):
    return await collect(list(BY_ID), response)

@router.get("/{service_id}", response_model=Observation)
async def get_service(service_id: str, response: Response):
    if service_id not in BY_ID:
        raise HTTPException(404, "Service not found")
    return (await collect([service_id], response)).services[0]
