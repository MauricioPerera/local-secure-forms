import json

import pytest

from src.lsfa.client import VerifiedConfirmation
from src.lsfa import cloudpress_verifier as verifier


class MemoryKeyring:
    def __init__(self): self.values = {}
    def get_password(self, service, profile): return self.values.get((service, profile))
    def set_password(self, service, profile, value): self.values[(service, profile)] = value


def test_factor_record_is_parseable_and_uses_scrypt():
    raw = verifier.encode_record("un-pin-seguro", "JBSWY3DPEHPK3PXP")
    stored = json.loads(raw)
    record = verifier.decode_record(raw)
    assert stored["pin_hash"] != "un-pin-seguro"
    assert verifier.derive_pin("un-pin-seguro", record["salt"]) == record["pin_hash"]


def test_totp_accepts_current_window_but_not_other_code():
    secret, now = "JBSWY3DPEHPK3PXP", 1_700_000_000
    assert verifier.verify_totp(secret, verifier.totp_code(secret, now), now)
    assert not verifier.verify_totp(secret, "000000", now)


def test_verifier_requires_explicit_approval_pin_and_totp(monkeypatch):
    backend = MemoryKeyring()
    backend.set_password(verifier.SERVICE, "default", verifier.encode_record("un-pin-seguro", "JBSWY3DPEHPK3PXP"))
    original_load_record = verifier.load_record
    monkeypatch.setattr(verifier, "load_record", lambda profile: original_load_record(profile, backend))
    now = 1_700_000_000
    monkeypatch.setattr(verifier.time, "time", lambda: now)
    monkeypatch.setattr(verifier, "local_approval_dialog", lambda summary, method, record: method == "pin_and_totp" and record["totp_secret"] == "JBSWY3DPEHPK3PXP")
    receipt = verifier.verifier_for_profile()( {"operation": "purge_content", "target": {"id": 7}}, "pin_and_totp", "a" * 64, now + 120)
    assert isinstance(receipt, VerifiedConfirmation)
    assert receipt.binding == "a" * 64


def test_verifier_fails_closed_when_user_does_not_approve(monkeypatch):
    monkeypatch.setattr(verifier, "local_approval_dialog", lambda *_args: False)
    assert verifier.verifier_for_profile()({}, "pin", "a" * 64, 2_000_000_000) is None


def test_approval_summary_is_human_readable_and_does_not_render_json():
    result = verifier.approval_summary({"operation": "purge_content", "target": {"id": 7, "title": "Borrador de prueba"}})
    assert "Eliminar permanentemente contenido" in result
    assert "Título: Borrador de prueba" in result
    assert '"operation"' not in result


def test_documented_verify_callback_is_directly_invocable(monkeypatch):
    monkeypatch.setattr(verifier, "verifier_for_profile", lambda: lambda *args: "receipt")
    assert verifier.verify({}, "pin", "binding", 100) == "receipt"


def test_profile_and_record_validation_fail_closed():
    with pytest.raises(ValueError): verifier.validate_profile("../other")
    with pytest.raises(ValueError): verifier.decode_record("not-json")
