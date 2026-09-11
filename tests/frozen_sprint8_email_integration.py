"""Pruebas congeladas del contrato de integración de correo."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_email_integration_spec_freezes_safe_operations():
    text = (ROOT / "specs" / "lsfa-email-integration.md").read_text(encoding="utf-8")
    for marker in ("connect_email", "send_email", "IMAP/SMTP", "SMTP", "contraseña", "opacas", "cancelación", "rechazo", "expiración"):
        assert marker in text
    assert "nunca forma parte del resultado" in text


def test_contract_freezes_email_security_boundary():
    text = (ROOT / "knowledge" / "contracts" / "sprint8-email-integration.md").read_text(encoding="utf-8")
    assert "task: sprint8_email_integration" in text
    assert "tests: tests/frozen_sprint8_email_integration.py" in text
    assert "PARAR y reportar si" in text
    assert "SMTP sin la confirmación" in text
