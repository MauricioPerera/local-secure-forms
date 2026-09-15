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
    monkeypatch.setattr("builtins.input", lambda _prompt: "APROBAR")
    monkeypatch.setattr(verifier.getpass, "getpass", lambda _prompt: "un-pin-seguro" if "PIN" in _prompt else verifier.totp_code("JBSWY3DPEHPK3PXP", now))
    receipt = verifier.verify()( {"operation": "purge_content", "target": {"id": 7}}, "pin_and_totp", "a" * 64, now + 120)
    assert isinstance(receipt, VerifiedConfirmation)
    assert receipt.binding == "a" * 64


def test_verifier_fails_closed_when_user_does_not_approve(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _prompt: "no")
    assert verifier.verify()({}, "pin", "a" * 64, 2_000_000_000) is None


def test_profile_and_record_validation_fail_closed():
    with pytest.raises(ValueError): verifier.validate_profile("../other")
    with pytest.raises(ValueError): verifier.decode_record("not-json")
