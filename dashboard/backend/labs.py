"""Read-only catalog discovery from trusted local repository files."""
import json
from pathlib import Path
import re
from collections import Counter
from typing import Literal
import yaml
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from tools.validate_manifest import ROOT, load_manifest

router = APIRouter(prefix="/api/v1/labs", tags=["labs"])

class Control(BaseModel):
    id: str
    name: str
    objective: str
    enforcement_point: str

class Expected(BaseModel):
    http_status: int

class Scenario(BaseModel):
    id: str
    title: str
    controls: list[str]
    action: str
    expected: Expected

class Lab(BaseModel):
    id: str
    title: str
    description: str
    schema_version: Literal[1]
    manual_path: str
    services: list[str]
    scenarios: list[Scenario]
    controls: list[Control]

class Issue(BaseModel):
    directory: str
    reason: str

class Catalog(BaseModel):
    labs: list[Lab]
    issues: list[Issue]

def discover(root: Path = ROOT / "labs") -> Catalog:
    # Root is server-selected, never supplied by HTTP clients.
    if root.is_symlink() or not root.is_dir():
        raise OSError("Lab root unavailable")
    controls = json.loads((ROOT / "docs/controls/controls.json").read_text(encoding="utf-8"))["controls"]
    by_id = {c["id"]: Control(**c) for c in controls}
    if len(by_id) != len(controls):
        raise ValueError("Duplicate catalog controls")
    candidates = []
    issues = []
    for folder in sorted(root.iterdir()):
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,100}", folder.name):
            continue
        if folder.is_symlink() or getattr(folder, "is_junction", lambda: False)():
            issues.append(Issue(directory=folder.name, reason="Linked directory rejected"))
            continue
        if not folder.is_dir():
            continue
        manifest = folder / "manifest.yaml"
        if not manifest.exists() and not manifest.is_symlink():
            continue
        try:
            manual = folder / "README.md"
            for path in (manifest, manual):
                if path.is_symlink() or not path.is_file() or path.resolve().parent != folder.resolve():
                    raise ValueError("Unsafe or missing file")
            if folder.resolve().parent != root.resolve() or manifest.stat().st_size > 100000:
                raise ValueError("Unsafe path or oversized manifest")
            data = load_manifest(manifest)
            ids = sorted({c for s in data["scenarios"] for c in s["controls"]})
            candidates.append((folder.name, Lab(**data, manual_path=f"labs/{folder.name}/README.md", controls=[by_id[c] for c in ids])))
        except (OSError, ValueError, yaml.YAMLError, RecursionError, KeyError, TypeError):
            issues.append(Issue(directory=folder.name, reason="Invalid or unreadable manifest or manual"))
    counts = Counter(lab.id for _, lab in candidates)
    labs = []
    for folder, lab in candidates:
        if counts[lab.id] > 1:
            issues.append(Issue(directory=folder, reason="Duplicate lab ID"))
        else:
            labs.append(lab)
    return Catalog(labs=sorted(labs, key=lambda lab: lab.id), issues=issues)

def catalog_or_error():
    try:
        return discover()
    except (OSError, ValueError, KeyError, TypeError):
        raise HTTPException(503, "Lab catalog unavailable") from None

@router.get("", response_model=Catalog)
def list_labs(response: Response):
    response.headers["Cache-Control"] = "no-store"
    return catalog_or_error()

@router.get("/{lab_id}", response_model=Lab)
def get_lab(lab_id: str, response: Response):
    response.headers["Cache-Control"] = "no-store"
    for lab in catalog_or_error().labs:
        if lab.id == lab_id:
            return lab
    raise HTTPException(404, "Lab not found")
