import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_attachment_example_is_explicitly_authorized():
    data = json.loads((ROOT / "examples/extract-attachment.json").read_text(encoding="utf-8"))
    assert data["operation"] == "extract_attachment"
    assert data["confirmation"] == {
        "method": "user_accept",
        "required": True,
        "single_use": True,
    }
    assert all("value" not in field for field in data["fields"])


def test_attachment_spec_preserves_metadata_bytes_boundary():
    text = (ROOT / "specs/lsfa-attachments.md").read_text(encoding="utf-8").lower()
    assert "sin autorización no se escribe ningún byte" in text
    assert "nunca compone una ruta" in text
    assert "nunca devuelve bytes" in text
    assert "idempotente" in text


def test_attachment_contract_forbids_external_validation():
    text = (ROOT / "knowledge/contracts/sprint12-attachments.md").read_text(encoding="utf-8").lower()
    assert "status: frozen" in text
    assert "parar y reportar" in text
    assert "no se ejecutan descargas reales" in text
