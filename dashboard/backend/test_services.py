import asyncio
import json
import unittest
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from dashboard.backend.main import app
from dashboard.backend.services import BY_ID, MAX_BODY, observe

class Body(httpx.AsyncByteStream):
    def __init__(self, data):
        self.data = data
    async def __aiter__(self):
        yield self.data

def reply(data, code=200, headers=None):
    return httpx.Response(code, stream=Body(json.dumps(data).encode()), headers=headers)

class ProbeTests(unittest.IsolatedAsyncioTestCase):
    async def run_probe(self, handler, ids=("registry",)):
        return (await observe(ids, httpx.MockTransport(handler))).services

    async def test_available(self):
        rows = await self.run_probe(lambda r: reply({"ok":True,"mode":"registry"}))
        self.assertEqual(rows[0].status,"available")
        self.assertEqual(rows[0].control_effectiveness,"not_assessed")
        self.assertEqual(rows[0].http_status,200)

    async def test_wrong_mode_and_false_ok(self):
        for data in ({"ok":True,"mode":"gateway"},{"ok":False,"mode":"registry"},[]):
            self.assertEqual((await self.run_probe(lambda r: reply(data)))[0].status,"unknown")

    async def test_unknown_internal(self):
        def forbidden(r):
            self.fail("Internal service must not be probed")
        rows = await self.run_probe(forbidden, ("opa","spire-server","spire-agent"))
        self.assertTrue(all(r.status=="unknown" and r.duration_ms is None for r in rows))

    async def test_http_failure(self):
        row = (await self.run_probe(lambda r: reply({},503)))[0]
        self.assertEqual((row.status,row.http_status),("unavailable",503))

    async def test_no_redirect(self):
        calls=[]
        def handler(r):
            calls.append(str(r.url))
            self.assertEqual(r.method,"GET")
            self.assertNotIn("authorization",r.headers)
            return reply({},302,{"Location":"http://example.invalid"})
        row=(await self.run_probe(handler))[0]
        self.assertEqual(calls,[BY_ID["registry"].url])
        self.assertEqual(row.status,"unavailable")

    async def test_transport_failure(self):
        def handler(r):
            raise httpx.ConnectError("sensitive-marker",request=r)
        row=(await self.run_probe(handler))[0]
        self.assertEqual(row.status,"unavailable")
        self.assertNotIn("sensitive-marker",str(row))

    async def test_deadline(self):
        async def handler(r):
            await asyncio.sleep(1)
            return reply({})
        with patch("dashboard.backend.services.DEADLINE",0.02):
            row=(await self.run_probe(handler))[0]
        self.assertEqual(row.reason,"Probe timed out")

    async def test_invalid_and_large_body(self):
        for raw in (b"not json",b"x"*(MAX_BODY+1)):
            row=(await self.run_probe(lambda r:httpx.Response(200,stream=Body(raw))))[0]
            self.assertEqual(row.status,"unknown")

    async def test_encoding(self):
        row=(await self.run_probe(lambda r:reply({},headers={"Content-Encoding":"gzip"})))[0]
        self.assertEqual(row.status,"unknown")

    async def test_keycloak_and_openbao(self):
        def handler(r):
            if r.url.port==8081:
                return reply({"issuer":"http://127.0.0.1:8081/realms/agent-lab","token_endpoint":"http://127.0.0.1:8081/token"})
            return reply({"initialized":True,"sealed":False,"standby":False})
        rows=await self.run_probe(handler,("keycloak","openbao"))
        self.assertEqual([r.status for r in rows],["available","available"])
        row=(await self.run_probe(lambda r:reply({"initialized":True,"sealed":True,"standby":False},503),("openbao",)))[0]
        self.assertEqual(row.status,"unavailable")

class ServiceApiTests(unittest.TestCase):
    def test_api_contract(self):
        async def fake(ids):
            return await observe(ids,httpx.MockTransport(lambda r:reply({},503)))
        with patch("dashboard.backend.services.observe",side_effect=fake), TestClient(app) as client:
            response=client.get("/api/v1/services")
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.headers["cache-control"],"no-store")
            rows=response.json()["services"]
            self.assertEqual(len(rows),7)
            self.assertEqual(client.get("/api/v1/services/opa").json()["status"],"unknown")
            self.assertEqual(client.get("/api/v1/services/unknown").status_code,404)
            self.assertEqual(client.post("/api/v1/services").status_code,405)
            self.assertTrue(all(r["control_effectiveness"]=="not_assessed" for r in rows))

    def test_overlap(self):
        with patch("dashboard.backend.services.gate.locked",return_value=True), TestClient(app) as client:
            self.assertEqual(client.get("/api/v1/services").status_code,429)
