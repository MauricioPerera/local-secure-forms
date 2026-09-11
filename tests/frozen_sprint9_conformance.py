"""Pruebas congeladas del kit de conformidad LSFA."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_conformance_validator_and_required_artifacts_exist():
    assert (ROOT / "scripts" / "validate_conformance.py").is_file()
    assert (ROOT / "CONFORMANCE.md").is_file()
    for name in ("request.schema.json", "result.schema.json", "confirmation.schema.json", "lifecycle.schema.json"):
        json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def test_conformance_guide_freezes_two_levels_and_no_certification_claim():
    text = (ROOT / "CONFORMANCE.md").read_text(encoding="utf-8")
    for marker in ("Nivel 1", "Nivel 2", "no expone secretos", "Linux", "Windows", "certificación externa"):
        assert marker in text


def test_contract_freezes_deterministic_security_boundary():
    text = (ROOT / "knowledge" / "contracts" / "sprint9-conformance-kit.md").read_text(encoding="utf-8")
    assert "task: sprint9_conformance_kit" in text
    assert "tests: tests/frozen_sprint9_conformance.py" in text
    assert "PARAR y reportar si" in text
    assert "no usa red ni modelos" in text
