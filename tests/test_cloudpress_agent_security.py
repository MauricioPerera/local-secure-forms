import importlib.util
import json
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest


SPEC = importlib.util.spec_from_file_location("cloudpress_broker_security", Path(__file__).parents[1] / "examples" / "cloudpress_loopback_broker.py")
BROKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BROKER)
ORIGIN = "https://cms.example"


def stored(channel="channel-token-abcdefghijklmnopqrstuvwxyz123456"):
    return json.dumps({
        "id": "capability-qa",
        "token": "A" * 44,
        "channel_token": channel,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
    })


def test_channel_token_not_origin_authenticates_local_agent(monkeypatch):
    monkeypatch.setattr(BROKER.keyring, "get_password", lambda _service, _origin: stored())
    assert BROKER.channel_authorized(ORIGIN, "channel-token-abcdefghijklmnopqrstuvwxyz123456") is True
    assert BROKER.channel_authorized(ORIGIN, "forged-origin-is-not-enough") is False
    status = BROKER.agent_status(ORIGIN, "channel-token-abcdefghijklmnopqrstuvwxyz123456")
    assert status["linked"] is True and status["authorized"] is True
    assert "token" not in status and "channel_token" not in status


def test_agent_proxy_uses_explicit_route_and_method_policy():
    assert BROKER.agent_request_allowed("/api/admin/users", "GET") is True
    assert BROKER.agent_request_allowed("/api/admin/trash/7", "POST") is True
    assert BROKER.agent_request_allowed("/api/admin/export", "GET") is False
    assert BROKER.agent_request_allowed("/api/admin/settings", "GET") is False
    assert BROKER.agent_request_allowed("/api/admin/users", "POST") is False
    assert BROKER.agent_request_allowed("/api/admin/users/7", "PATCH") is False
    assert BROKER.agent_request_allowed("/api/admin/users/7/active", "POST") is True
    assert BROKER.agent_request_allowed("/api/admin/agent-execution", "POST") is True
    assert BROKER.agent_request_allowed("/api/admin/agent-runtime", "POST", {"action": "claim"}) is True
    assert BROKER.agent_request_allowed("/api/admin/agent-runtime", "POST", {"action": "erase_everything"}) is False
    assert BROKER.agent_request_allowed("/api/admin/agent-runtime", "POST") is False
    assert BROKER.agent_request_allowed("/api/admin/plugins/demo-plugin/privacy/2", "GET") is False


def test_agent_execution_context_is_bounded_and_not_a_header_passthrough():
    headers = BROKER.agent_execution_headers({"taskId": "00000000-0000-0000-0000-000000000000", "ordinal": 7})
    assert headers == {"X-CloudPress-Task-Id": "00000000-0000-0000-0000-000000000000", "X-CloudPress-Step-Ordinal": "7"}
    for value in ({"taskId": "not-a-task", "ordinal": 1}, {"taskId": "00000000-0000-0000-0000-000000000000", "ordinal": 0}, {"Authorization": "Bearer injected"}):
        with pytest.raises(ValueError, match="invalid_agent_execution"):
            BROKER.agent_execution_headers(value)


def test_non_json_remote_error_is_structured(monkeypatch):
    monkeypatch.setattr(BROKER.keyring, "get_password", lambda _service, _origin: stored())

    class Response:
        status = 502

        def read(self):
            return b"<html>proxy error</html>"

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(BROKER, "urlopen", lambda *_args, **_kwargs: Response())
    status, body = BROKER.agent_api_request({"protocol": "lsfa", "version": "0.2", "origin": ORIGIN, "request": {"path": "/api/admin/users", "method": "GET"}}, ORIGIN)
    assert status == 502
    assert body == {"error": "cloudpress_non_json_response", "remoteStatus": 502}


def test_http_proxy_rejects_forged_origin_without_channel(monkeypatch):
    monkeypatch.setattr(BROKER.keyring, "get_password", lambda _service, _origin: stored())
    monkeypatch.setattr(BROKER, "agent_api_request", lambda _payload, _origin: (200, {"items": []}))
    server = ThreadingHTTPServer(("127.0.0.1", 0), BROKER.make_handler(None, None, ORIGIN))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.server_port}/v1/cloudpress/agent-api"
    body = json.dumps({"protocol": "lsfa", "version": "0.2", "origin": ORIGIN, "request": {"path": "/api/admin/users", "method": "GET"}}).encode()
    try:
        with pytest.raises(HTTPError) as rejected:
            urlopen(Request(endpoint, method="POST", data=body, headers={"Origin": ORIGIN, "Content-Type": "application/json"}), timeout=2)
        assert rejected.value.code == 401
        accepted = urlopen(Request(endpoint, method="POST", data=body, headers={"Origin": ORIGIN, "Content-Type": "application/json", "X-LSFA-Channel-Token": "channel-token-abcdefghijklmnopqrstuvwxyz123456"}), timeout=2)
        assert accepted.status == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_cloudpress_origin_rejects_credentials_paths_and_queries():
    assert BROKER.validate_cloudpress_origin(ORIGIN) == ORIGIN
    for value in (
        "https://cms.example/",
        "https://cms.example/admin",
        "https://cms.example?next=https://attacker.example",
        "https://cms.example#fragment",
        "https://cms.example@attacker.example",
        "http://cms.example",
    ):
        with pytest.raises(ValueError, match="invalid_cloudpress_origin"):
            BROKER.validate_cloudpress_origin(value)


def test_outbound_cloudpress_request_rejects_redirect_without_forwarding_bearer():
    received = []

    class Target(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            received.append(self.headers.get("Authorization"))
            self.send_response(200)
            self.end_headers()

        def log_message(self, _format, *_args):
            return

    target = ThreadingHTTPServer(("127.0.0.1", 0), Target)

    class Redirect(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{target.server_port}/capture")
            self.end_headers()

        def log_message(self, _format, *_args):
            return

    redirect = ThreadingHTTPServer(("127.0.0.1", 0), Redirect)
    threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in (target, redirect)]
    for thread in threads:
        thread.start()
    try:
        request = Request(f"http://127.0.0.1:{redirect.server_port}/start", headers={"Authorization": "Bearer must-not-leak"})
        with pytest.raises(HTTPError) as rejected:
            BROKER.urlopen(request, timeout=2)
        assert rejected.value.code == 302
        assert received == []
    finally:
        for server in (redirect, target):
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(timeout=2)
