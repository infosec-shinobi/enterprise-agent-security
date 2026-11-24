"""A03: trusted, host-local HTTP actions. No lifecycle mutations."""
from dataclasses import dataclass
import json
import os
import httpx

TOKEN_URL = "http://localhost:8081/realms/agent-lab/protocol/openid-connect/token"
RECORD_URL = "http://localhost:8001/tools/records/123"
ACTIONS = {
    "lab-01-unregistered-read": "GET",
    "lab-01-draft-read": "GET",
    "lab-01-active-read": "GET",
    "lab-01-active-delete": "DELETE",
    "lab-01-suspended-read": "GET",
}


class RunnerError(Exception):
    """Only fixed, non-secret diagnostic messages."""


@dataclass(frozen=True)
class Result:
    outcome: str
    expected: int
    actual: int | None
    reason: str


class HttpRunner:
    def __init__(self, transport=None):
        self.client = httpx.Client(timeout=httpx.Timeout(5.0),
                                   follow_redirects=False, trust_env=False,
                                   transport=transport)
        self._token = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._token = None
        self.client.close()

    def authenticate(self):
        self._token = None
        try:
            response = self.client.post(TOKEN_URL, data={
                "grant_type": "client_credentials",
                "client_id": "agent-demo",
                "client_secret": os.getenv("LAB_CLIENT_SECRET", "local-demo-secret"),
            })
            if response.status_code != 200:
                raise RunnerError("Token endpoint rejected request")
            token = response.json()["access_token"]
            if not isinstance(token, str) or not token or not token.isascii() or any(c.isspace() for c in token):
                raise RunnerError("Invalid token response")
            self._token = token
        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            raise RunnerError("Token acquisition failed") from None

    def execute(self, action: str, expected: int) -> Result:
        if action not in ACTIONS:
            return Result("error", expected, None, "Unknown action")
        if not self._token:
            return Result("error", expected, None, "Authentication required")
        try:
            with self.client.stream(ACTIONS[action], RECORD_URL,
                                    headers={"Authorization": "Bearer " + self._token}) as response:
                actual = response.status_code
        except httpx.TimeoutException:
            return Result("error", expected, None, "HTTP timeout")
        except httpx.HTTPError:
            return Result("error", expected, None, "HTTP transport failure")
        if actual == expected:
            return Result("pass", expected, actual, "Expected status received")
        if actual == 401:
            return Result("error", expected, actual, "Authentication rejected")
        if actual >= 500:
            return Result("error", expected, actual, "Service or dependency failure")
        return Result("fail", expected, actual, "Unexpected HTTP status")
