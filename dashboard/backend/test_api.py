import unittest
from fastapi.testclient import TestClient
from dashboard.backend.main import app

class ApiTests(unittest.TestCase):
    def test_health(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/api/v1/health").json(), {
                "status":"ok","service":"playground-api","api_version":"v1"})

    def test_capabilities(self):
        with TestClient(app) as client:
            response = client.get("/api/v1/capabilities")
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.json(),dict(lab_discovery=True,service_health=True,execution=False,evidence=False,framework_mapping=False))

    def test_no_execution(self):
        with TestClient(app) as client:
            self.assertEqual(client.post("/api/v1/runs").status_code,404)

    def test_untrusted_host(self):
        with TestClient(app) as client:
            self.assertEqual(client.get("/api/v1/health",headers={"Host":"example.invalid"}).status_code,400)
