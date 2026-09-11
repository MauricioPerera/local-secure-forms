"""Pruebas congeladas del modelo de riesgo y confirmación LSFA."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_confirmation_schema_freezes_methods_and_single_use():
    schema = json.loads((ROOT / "schemas" / "confirmation.schema.json").read_text(encoding="utf-8"))
    assert schema["required"] == ["method", "required"]
    assert schema["properties"]["method"]["enum"] == ["user_accept", "pin", "pin_and_totp"]
    assert schema["properties"]["single_use"]["const"] is True
    assert schema["additionalProperties"] is False


def test_spec_freezes_risk_matrix_and_agent_boundary():
    text = (ROOT / "specs" / "lsfa-confirmation.md").read_text(encoding="utf-8")
    for value in ("`low`", "`medium`", "`high`", "`irreversible`", "PIN", "segundo factor", "una vez"):
        assert value in text
    assert "El agente no" in text
    assert "no ejecuta" in text


def test_contract_freezes_human_confirmation_safety_rules():
    text = (ROOT / "knowledge" / "contracts" / "sprint3-risk-confirmation.md").read_text(encoding="utf-8")
    assert "task: sprint3_risk_confirmation" in text
    assert "tests: tests/frozen_sprint3_confirmation.py" in text
    assert "PARAR y reportar si" in text
    assert "irreversible" in text and "pin_and_totp" in text
