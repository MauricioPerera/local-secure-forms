import importlib.util
import json
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


def test_agent_capability_requires_exact_origin_and_agent_proxy_rejects_purge(monkeypatch):
    expires = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    payload = {"protocol": "lsfa", "version": "0.2", "origin": "https://cms.example", "capability": {"id": "capability-qa-0001", "token": "A" * 44, "expires_at": expires}}
    request, values = BROKER.parse_agent_capability_payload(payload, "https://cms.example")
    assert request.operation == "cloudpress_agent_access"
    assert values["capability_token"] == "A" * 44
    monkeypatch.setattr(BROKER, "load_record", lambda _profile: {"enrolled": True})
    saved = {}
    monkeypatch.setattr(BROKER.keyring, "set_password", lambda service, account, value: saved.update(service=service, account=account, value=value))
    assert BROKER.store_agent_capability(payload, "https://cms.example")["status"] == "accepted"
    assert saved["service"] == BROKER.AGENT_CAPABILITY_SERVICE
    assert "A" * 44 in saved["value"]
    with pytest.raises(ValueError, match="operation_not_allowed"):
        BROKER.agent_api_request({"protocol": "lsfa", "version": "0.2", "origin": "https://cms.example", "request": {"path": "/api/admin/trash/7", "method": "DELETE", "body": {}}}, "https://cms.example")


def test_agent_status_reports_enrollment_without_exposing_capability(monkeypatch):
    monkeypatch.setattr(BROKER, "load_record", lambda _profile: {"enrolled": True})
    monkeypatch.setattr(BROKER.keyring, "get_password", lambda _service, _account: json.dumps({"id": "capability-qa-0001", "token": "A" * 44, "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()}))
    status = BROKER.agent_status("https://cms.example")
    assert status["enrolled"] is True and status["linked"] is True
    assert "token" not in status


def test_agent_capability_allows_bounded_clock_skew():
    expires = (datetime.now(timezone.utc) + timedelta(days=7, hours=12)).isoformat()
    payload = {"protocol": "lsfa", "version": "0.2", "origin": "https://cms.example", "capability": {"id": "capability-qa-0002", "token": "A" * 44, "expires_at": expires}}
    assert BROKER.parse_agent_capability_payload(payload, "https://cms.example")[0].operation == "cloudpress_agent_access"


def test_agent_proxy_identifies_the_companion(monkeypatch):
    monkeypatch.setattr(BROKER.keyring, "get_password", lambda _service, _origin: json.dumps({"token": "A" * 44, "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()}))
    captured = {}
    class Response:
        status = 200
        def read(self): return b'{"items":[]}'
        def __enter__(self): return self
        def __exit__(self, *_args): return False
    def fake_urlopen(request, timeout):
        captured["user_agent"] = request.get_header("User-agent")
        return Response()
    monkeypatch.setattr(BROKER, "urlopen", fake_urlopen)
    assert BROKER.agent_api_request({"protocol": "lsfa", "version": "0.2", "origin": "https://cms.example", "request": {"path": "/api/admin/entries", "method": "GET"}}, "https://cms.example")[0] == 200
    assert captured["user_agent"] == BROKER.COMPANION_USER_AGENT


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
