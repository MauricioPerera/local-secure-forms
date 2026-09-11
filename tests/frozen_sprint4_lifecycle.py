"""Pruebas congeladas del ciclo de vida destructivo LSFA."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_lifecycle_schema_freezes_operations_and_confirmation():
    schema = json.loads((ROOT / "schemas" / "lifecycle.schema.json").read_text(encoding="utf-8"))
    assert schema["properties"]["operation"]["enum"] == ["soft_delete", "restore", "purge"]
    assert schema["properties"]["confirmation"]["enum"] == ["user_accept", "pin", "pin_and_totp"]
    assert schema["additionalProperties"] is False


def test_lifecycle_spec_freezes_recovery_and_partial_failure():
    text = (ROOT / "specs" / "lsfa-lifecycle.md").read_text(encoding="utf-8")
    for marker in ("soft_delete", "restore", "purge", "rollback", "recovery_required", "irreversible", "pin_and_totp"):
        assert marker in text
    assert "nunca debe reportar" in text


def test_contract_freezes_purge_safety_boundary():
    text = (ROOT / "knowledge" / "contracts" / "sprint4-reversible-actions.md").read_text(encoding="utf-8")
    assert "task: sprint4_reversible_actions" in text
    assert "tests: tests/frozen_sprint4_lifecycle.py" in text
    assert "PARAR y reportar si" in text
    assert "purge" in text and "pin_and_totp" in text
