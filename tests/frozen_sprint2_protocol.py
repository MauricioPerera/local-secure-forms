"""Pruebas congeladas del contrato del protocolo base LSFA."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATES = {"accepted", "declined", "cancelled", "invalid", "failed", "expired"}


def _load(name):
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def test_request_schema_freezes_required_protocol_fields():
    schema = _load("request.schema.json")
    assert schema["required"] == ["operation", "purpose", "fields", "validation", "expires_in_seconds"]
    assert schema["properties"]["expires_in_seconds"]["maximum"] == 86400
    field = schema["properties"]["fields"]["items"]
    assert field["properties"]["sensitivity"]["enum"] == ["public", "private", "secret"]


def test_result_schema_freezes_states_and_secret_free_result_shape():
    schema = _load("result.schema.json")
    assert set(schema["properties"]["status"]["enum"]) == STATES
    assert "secret" not in schema["properties"]
    assert schema["additionalProperties"] is False


def test_specs_and_contract_agree_on_expiration_and_no_secret_result():
    request = (ROOT / "specs" / "lsfa-request.md").read_text(encoding="utf-8")
    result = (ROOT / "specs" / "lsfa-result.md").read_text(encoding="utf-8")
    contract = (ROOT / "knowledge" / "contracts" / "sprint2-protocol-base.md").read_text(encoding="utf-8")
    for text in (request, result, contract):
        assert "secret" in text
        assert "expir" in text.lower()
    assert "PARAR y reportar si" in contract
