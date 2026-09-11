"""Validador determinista del kit de conformidad LSFA 0.2."""

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SCHEMAS = {"request.schema.json", "result.schema.json", "confirmation.schema.json", "lifecycle.schema.json"}
REQUIRED_DOCS = {"SPEC.md", "SECURITY.md", "THREAT-MODEL.md", "UX-GUIDE.md", "STYLE-GUIDE.md", "CONFORMANCE.md"}


def main():
    missing = [name for name in REQUIRED_SCHEMAS if not (ROOT / "schemas" / name).is_file()]
    missing += [name for name in REQUIRED_DOCS if not (ROOT / name).is_file()]
    if missing:
        raise ValueError("faltan artefactos: " + ", ".join(sorted(missing)))
    for path in (ROOT / "schemas").glob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))
    examples = sorted((ROOT / "examples").glob("*.json"))
    if not examples:
        raise ValueError("no hay ejemplos")
    print(f"OK: conformidad estructural LSFA; {len(examples)} ejemplos y {len(REQUIRED_SCHEMAS)} esquemas")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
