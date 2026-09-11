"""Valida ejemplos JSON contra el contrato mínimo LSFA 0.2."""

import json
from pathlib import Path
import sys

RISKS = {"low", "medium", "high", "irreversible"}
STATUSES = {"accepted", "declined", "cancelled", "invalid", "failed", "expired"}


def validate_request(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {"operation", "purpose", "fields", "validation", "expires_in_seconds"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"{path}: faltan campos {sorted(missing)}")
    if data.get("risk", "medium") not in RISKS:
        raise ValueError(f"{path}: risk inválido")
    if not isinstance(data["fields"], list) or not data["fields"]:
        raise ValueError(f"{path}: fields debe ser una lista no vacía")
    for field in data["fields"]:
        if not {"name", "type", "sensitivity"} <= field.keys():
            raise ValueError(f"{path}: campo incompleto")
        if field["sensitivity"] == "secret" and "default" in field:
            raise ValueError(f"{path}: un secreto no puede tener default")
    if not isinstance(data["expires_in_seconds"], int) or data["expires_in_seconds"] <= 0:
        raise ValueError(f"{path}: expiración inválida")
    if data.get("risk") in {"high", "irreversible"}:
        confirmation = data.get("confirmation", {})
        if not confirmation.get("required"):
            raise ValueError(f"{path}: falta confirmación para riesgo elevado")
    return data


def main():
    root = Path(__file__).resolve().parents[1]
    paths = sorted((root / "examples").glob("*.json"))
    for path in paths:
        validate_request(path)
    print(f"OK: {len(paths)} ejemplos LSFA validos")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
