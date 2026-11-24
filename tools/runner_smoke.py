"""Run one manifest scenario against manually prepared local state."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
from http_runner import HttpRunner, RunnerError
from validate_manifest import load_manifest, ROOT

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario")
    args = parser.parse_args()
    try:
        manifest = load_manifest(ROOT / "labs/01-control-plane/manifest.yaml")
        scenario = next((s for s in manifest["scenarios"] if s["id"] == args.scenario), None)
        if scenario is None:
            raise RunnerError("Unknown scenario")
        with HttpRunner() as runner:
            runner.authenticate()
            result = runner.execute(scenario["action"], scenario["expected"]["http_status"])
        print(json.dumps(asdict(result)))
        return {"pass": 0, "fail": 1, "error": 2}[result.outcome]
    except (RunnerError, ValueError, OSError):
        print("Execution error: manifest or authentication unavailable")
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
