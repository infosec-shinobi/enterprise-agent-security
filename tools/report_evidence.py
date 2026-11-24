"""Read and validate a stored evidence report without executing a lab."""
import argparse
import json
from pathlib import Path
from jsonschema import ValidationError
import evidence

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        run = json.loads(args.file.read_text(encoding="utf-8"))
        evidence.validate(run)
    except (OSError, ValueError, ValidationError):
        print("ERROR: invalid or unavailable evidence")
        return 2
    if args.json:
        print(json.dumps(run, indent=2))
    else:
        print(f'{run["lab_id"]} | {run["run_id"]} | {run["outcome"].upper()}')
        for row in run["scenarios"]:
            print(f'{row["scenario"]:22} {row["outcome"]:8} expected={row["expected"]} actual={row["actual"]}')
        print(f'Cleanup: {run["cleanup"]} | Duration: {run["duration_ms"]} ms')
        print(f'Reason: {run["reason"]}')
    return run["exit_code"]

if __name__ == "__main__":
    raise SystemExit(main())
