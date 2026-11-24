"""A04: disposable Compose project, ordered assertions, scoped cleanup."""
import argparse
from dataclasses import asdict
import json
import os
import subprocess
import time
import uuid

import httpx
import yaml
from http_runner import HttpRunner, RunnerError
from validate_manifest import ROOT, load_manifest

REGISTRY = "http://localhost:8000"
GATEWAY = "http://localhost:8001"
ORDER = [
    ("unregistered-read", None, 403),
    ("draft-read", "draft", 403),
    ("active-read", "active", 200),
    ("active-delete", None, 403),
    ("suspended-read", "suspended", 403),
]


def compose(project, *args, timeout=600):
    # Explicit file and project: never use the default project for cleanup.
    return subprocess.run(
        ["docker", "compose", "-f", str(ROOT / "compose.yaml"), "-p", project, *args],
        cwd=ROOT, timeout=timeout, check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def require_state(client, state):
    response = client.get(REGISTRY + "/internal/agents/agent-demo")
    if state is None:
        if response.status_code != 404:
            raise RunnerError("Fresh registry required")
    elif response.status_code != 200 or response.json().get("lifecycle") != state:
        raise RunnerError("Registry state verification failed")


def transition(client, state):
    path = "/agents/agent-demo?owner=lab-owner" if state == "draft" else "/agents/agent-demo/state/" + state
    response = client.post(REGISTRY + path, headers={
        "X-Lab-Admin-Key": os.getenv("LAB_ADMIN_KEY", "local-demo-admin-key")
    })
    if response.status_code != 200 or response.json().get("lifecycle") != state:
        raise RunnerError("Registry transition failed: " + state)
    require_state(client, state)


def ready(runner):
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        try:
            for url, mode in [(REGISTRY, "registry"), (GATEWAY, "gateway")]:
                response = runner.client.get(url + "/health")
                if response.status_code != 200 or response.json().get("mode") != mode:
                    raise RunnerError("Service not ready")
            runner.authenticate()
            return
        except (RunnerError, httpx.HTTPError, ValueError):
            time.sleep(2)
    raise RunnerError("Service readiness timed out")


def run_scenarios(runner, manifest):
    scenarios = manifest["scenarios"]
    expected_contract = [(s, "lab-01-" + s, status) for s, _, status in ORDER]
    if [(s["id"], s["action"], s["expected"]["http_status"]) for s in scenarios] != expected_contract:
        raise RunnerError("Unexpected Lab 01 scenario contract")
    require_state(runner.client, None)
    for scenario, (_, state, _) in zip(scenarios, ORDER):
        if state:
            transition(runner.client, state)
        elif scenario["id"] == "active-delete":
            require_state(runner.client, "active")
        result = runner.execute(scenario["action"], scenario["expected"]["http_status"])
        print(json.dumps({"scenario": scenario["id"], **asdict(result)}), flush=True)
        if result.outcome != "pass":
            return 1 if result.outcome == "fail" else 2
    return 0


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    project = "eas-a04-" + uuid.uuid4().hex
    started = False
    code = 2
    try:
        manifest = load_manifest(ROOT / "labs/01-control-plane/manifest.yaml")
        # Refuse occupied host ports before creating any resources; Compose
        # also enforces exclusive port bindings during startup.
        import socket
        for port in (8000, 8001, 8081):
            with socket.socket() as sock:
                sock.settimeout(1)
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    raise RunnerError("Host port occupied: " + str(port))
        print("Disposable project: " + project, flush=True)
        started = True
        compose(project, "up", "--build", "-d")
        with HttpRunner() as runner:
            ready(runner)
            code = run_scenarios(runner, manifest)
    except RunnerError as exc:
        print("ERROR: " + str(exc))
    except (httpx.HTTPError, ValueError, OSError, subprocess.SubprocessError, yaml.YAMLError):
        print("ERROR: manifest, HTTP or Compose operation failed")
    except KeyboardInterrupt:
        print("Interrupted")
    finally:
        if started:
            try:
                compose(project, "down", "-v", timeout=120)
                print("Cleanup complete: " + project)
            except (OSError, subprocess.SubprocessError, KeyboardInterrupt):
                print("Cleanup failed; inspect project: " + project)
                code = 2
    return code


if __name__ == "__main__":
    raise SystemExit(main())
