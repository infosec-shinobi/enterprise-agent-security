"""Validate a manifest without executing any actions."""
import argparse
import json
from pathlib import Path
import sys

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise ValueError("Non-string or duplicate YAML mapping key")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


def validate(data):
    schema = json.loads((ROOT / "schemas/lab-manifest.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: str(e.path))
    if errors:
        raise ValueError("; ".join(f"{e.json_path}: {e.message}" for e in errors))
    catalog = json.loads((ROOT / "docs/controls/controls.json").read_text(encoding="utf-8"))
    known = {c["id"] for c in catalog["controls"]}
    seen = set()
    for scenario in data["scenarios"]:
        if scenario["id"] in seen:
            raise ValueError("Duplicate scenario ID: " + scenario["id"])
        seen.add(scenario["id"])
        unknown = set(scenario["controls"]) - known
        if unknown:
            raise ValueError("Unknown controls: " + ", ".join(sorted(unknown)))


def load_manifest(path):
    raw = path.read_text(encoding="utf-8")
    if len(raw) > 100_000:
        raise ValueError("Manifest exceeds size limit")
    # Reject aliases/anchors to keep this simple data format bounded.
    if any(isinstance(t, (yaml.tokens.AliasToken, yaml.tokens.AnchorToken)) for t in yaml.scan(raw)):
        raise ValueError("YAML aliases and anchors are not supported")
    data = yaml.load(raw, Loader=UniqueLoader)
    validate(data)
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        load_manifest(args.manifest)
    except (ValueError, OSError, yaml.YAMLError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    sys.exit(main())
