import importlib.util
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


SPEC = importlib.util.spec_from_file_location("cloudpress_broker", Path(__file__).parents[1] / "examples" / "cloudpress_loopback_broker.py")
BROKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BROKER)


def payload():
    return {
        "protocol": "lsfa", "version": "0.2", "origin": "https://cms.example",
        "request": {"request_id": "approval-123", "operation": "cloudpress_irreversible_action", "risk": "irreversible", "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=3)).isoformat(), "summary": {"operation": "purge_content", "target": {"id": 7, "title": "QA"}}},
        "execute": {"url": "https://cms.example/api/admin/approvals/approval-123/execute", "token": "opaque-capability-token"},
    }

def recovery_payload():
    request_id = "recover-123"
    return {
        "protocol": "lsfa", "version": "0.2", "origin": "https://cms.example",
        "request": {"request_id": request_id, "operation": "cloudpress_totp_recovery", "risk": "high", "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=3)).isoformat(), "summary": {"operation": "recover_account", "username": "admin"}},
        "verify": {"url": f"https://cms.example/api/totp-recovery/{request_id}/verify", "token": "opaque-recovery-token"},
        "execute": {"url": f"https://cms.example/api/totp-recovery/{request_id}/complete"},
        "credentials": {"new_password": "Nueva-clave-segura", "totp_code": "123456", "recovery_code": ""},
    }


def test_cloudpress_payload_binds_exact_origin_url_and_irreversible_policy():
    request, values = BROKER.parse_cloudpress_payload(payload(), "https://cms.example")
    assert request.operation == "cloudpress_irreversible_action"
    assert request.risk == "irreversible"
    assert values["execution_token"] == "opaque-capability-token"


def test_cloudpress_payload_rejects_cross_origin_execution_url():
    changed = payload()
    changed["execute"] = {"url": "https://attacker.example/api/admin/approvals/approval-123/execute", "token": "opaque-capability-token"}
    with pytest.raises(ValueError, match="invalid_execute_url"):
        BROKER.parse_cloudpress_payload(changed, "https://cms.example")


def test_companion_requires_irreversible_verifier_and_never_returns_token(monkeypatch, tmp_path):
    request, values = BROKER.parse_cloudpress_payload(payload(), "https://cms.example")
    seen = []

    class Response:
        status = 200

        def read(self):
            return b'{"state":"accepted"}'

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def verifier(summary, method, binding, expires_at):
        seen.append((summary, method))
        return BROKER.VerifiedConfirmation(binding, method, expires_at)

    monkeypatch.setattr(BROKER, "urlopen", lambda request, timeout: Response())
    result = BROKER.result_for(BROKER.build_broker("https://cms.example", verifier, tmp_path / "authorizations.sqlite3"), request, values)
    assert result["status"] == "accepted"
    assert result["checks"] == {"executed": True}
    assert seen == [({"operation": "purge_content", "target": {"id": 7, "title": "QA"}}, "pin_and_totp")]
    assert "opaque-capability-token" not in str(result)


def test_totp_recovery_requires_server_otp_then_local_pin(monkeypatch, tmp_path):
    request, values = BROKER.parse_recovery_payload(recovery_payload(), "https://cms.example")
    seen, responses = [], [b'{"state":"verified"}', b'{"state":"used"}']

    class Response:
        status = 200
        def read(self):
            return responses.pop(0)
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False

    def verifier(summary, method, binding, expires_at):
        seen.append((summary, method))
        return BROKER.VerifiedConfirmation(binding, method, expires_at)

    monkeypatch.setattr(BROKER, "urlopen", lambda request, timeout: Response())
    result = BROKER.result_for(BROKER.build_recovery_broker("https://cms.example", verifier, tmp_path / "recovery.sqlite3"), request, values)
    assert result["status"] == "accepted"
    assert result["checks"] == {"recovered": True}
    assert seen == [({"operation": "recover_account", "username": "admin"}, "pin")]
    assert "opaque-recovery-token" not in str(result)


def test_totp_recovery_rejects_wrong_cloudpress_path():
    changed = recovery_payload()
    changed["execute"]["url"] = "https://cms.example/api/totp-recovery/recover-123/other"
    with pytest.raises(ValueError, match="invalid_execute_url"):
        BROKER.parse_recovery_payload(changed, "https://cms.example")


def test_boolean_verifier_is_not_a_confirmation_receipt(monkeypatch, tmp_path):
    request, values = BROKER.parse_cloudpress_payload(payload(), "https://cms.example")
    adapter = BROKER.build_broker("https://cms.example", lambda *_args: True, tmp_path / "authorizations.sqlite3")
    monkeypatch.setattr(BROKER, "urlopen", lambda *_args, **_kwargs: pytest.fail("No debe ejecutar sin recibo verificado"))
    result = BROKER.result_for(adapter, request, values)
    assert result["status"] == "failed"
    assert result["error_code"] == "request_failed"


def test_result_for_does_not_mutate_shared_adapter(monkeypatch, tmp_path):
    request, values = BROKER.parse_cloudpress_payload(payload(), "https://cms.example")

    class Response:
        status = 200
        def read(self): return b'{"state":"accepted"}'
        def __enter__(self): return self
        def __exit__(self, *_args): return False

    def verifier(_summary, method, binding, expires_at):
        return BROKER.VerifiedConfirmation(binding, method, expires_at)

    adapter = BROKER.build_broker("https://cms.example", verifier, tmp_path / "authorizations.sqlite3")
    original_collect = adapter.collect
    monkeypatch.setattr(BROKER, "urlopen", lambda *_args, **_kwargs: Response())
    assert BROKER.result_for(adapter, request, values)["status"] == "accepted"
    assert adapter.collect is original_collect
