"""Local read-only playground API. No lab execution in B03."""
from typing import Literal
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.middleware.trustedhost import TrustedHostMiddleware

from dashboard.backend.labs import router
from dashboard.backend.services import router as services_router

app = FastAPI(title="Enterprise Agent Security Playground", version="0.1.0")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1", "testserver"])

app.include_router(router)
app.include_router(services_router)

class Health(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["playground-api"] = "playground-api"
    api_version: Literal["v1"] = "v1"

@app.get("/api/v1/health", response_model=Health)
def health():
    return Health()

class Capabilities(BaseModel):
    lab_discovery: bool = True
    service_health: bool = True
    execution: bool = False
    evidence: bool = False
    framework_mapping: bool = False

@app.get("/api/v1/capabilities", response_model=Capabilities)
def capabilities():
    return Capabilities()
