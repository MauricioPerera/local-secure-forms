"""Companion LSFA de referencia para acciones irreversibles de CloudPress.

Escucha sólo en loopback y nunca devuelve el token opaco de ejecución al agente.
Requiere un verificador local real configurado por el integrador; no incluye un
PIN, TOTP ni una confirmación simulada.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen

# ``python examples/cloudpress_loopback_broker.py`` sets sys.path[0] to the
# examples directory. Add the repository root explicitly so the documented
# launcher resolves the local SDK instead of an unrelated installed package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.lsfa.adapters import TerminalAdapter
from src.lsfa.authorization import AuthorizationStore
from src.lsfa.client import LocalClient, OperationPolicy, VerifiedConfirmation
from src.lsfa.core import FieldSpec, LSFARequest, RiskLevel


REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
OPERATIONS = {"purge_content", "delete_user", "delete_media", "uninstall_plugin", "delete_metadata", "delete_core_term", "delete_plugin_term"}
FIELDS = (
    FieldSpec("summary", "multiline", "private", True),
    FieldSpec("execute_url", "text", "private", True),
    FieldSpec("execution_token", "secret", "secret", True),
)
RECOVERY_FIELDS = (
    FieldSpec("summary", "multiline", "private", True),
    FieldSpec("verify_url", "text", "private", True),
    FieldSpec("execute_url", "text", "private", True),
    FieldSpec("recovery_token", "secret", "secret", True),
    FieldSpec("new_password", "secret", "secret", True),
    FieldSpec("totp_code", "secret", "secret", False),
    FieldSpec("recovery_code", "secret", "secret", False),
)


def parse_cloudpress_payload(payload: object, cloudpress_origin: str) -> tuple[LSFARequest, dict]:
    """Construye una solicitud LSFA sólo desde el contrato local permitido."""
    if not isinstance(payload, dict) or payload.get("protocol") != "lsfa" or payload.get("version") != "0.2":
        raise ValueError("invalid_protocol")
    if payload.get("origin") != cloudpress_origin:
        raise ValueError("invalid_origin")
    request = payload.get("request")
    execute = payload.get("execute")
    if not isinstance(request, dict) or not isinstance(execute, dict):
        raise ValueError("invalid_request")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id):
        raise ValueError("invalid_request_id")
    if request.get("operation") != "cloudpress_irreversible_action" or request.get("risk") != "irreversible":
        raise ValueError("invalid_operation")
    summary = request.get("summary")
    if not isinstance(summary, dict) or summary.get("operation") not in OPERATIONS:
        raise ValueError("invalid_summary")
    token = execute.get("token")
    if not isinstance(token, str) or not 1 <= len(token) <= 128:
        raise ValueError("invalid_token")
    url = execute.get("url")
    expected_path = f"/api/admin/approvals/{request_id}/execute"
    parsed = urlparse(url if isinstance(url, str) else "")
    if f"{parsed.scheme}://{parsed.netloc}" != cloudpress_origin or parsed.path != expected_path or parsed.query or parsed.fragment:
        raise ValueError("invalid_execute_url")
    try:
        expires = datetime.fromisoformat(str(request["expires_at"]).replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("invalid_expiry") from error
    seconds = int((expires - datetime.now(timezone.utc)).total_seconds())
    if not 1 <= seconds <= 300:
        raise ValueError("expired_or_invalid_expiry")
    values = {"summary": json.dumps(summary, ensure_ascii=False, sort_keys=True), "execute_url": url, "execution_token": token}
    ticket = LSFARequest("cloudpress_irreversible_action", "Ejecutar exclusivamente la acción irreversible preparada por CloudPress.", FIELDS, {"preflight": "cloudpress_target"}, seconds, risk=RiskLevel.IRREVERSIBLE, request_id=request_id, initiator="agent", presentation="terminal")
    return ticket, values


def parse_recovery_payload(payload: object, cloudpress_origin: str) -> tuple[LSFARequest, dict]:
    """Acepta sólo una recuperación TOTP preparada por el origen configurado."""
    if not isinstance(payload, dict) or payload.get("protocol") != "lsfa" or payload.get("version") != "0.2":
        raise ValueError("invalid_protocol")
    if payload.get("origin") != cloudpress_origin:
        raise ValueError("invalid_origin")
    request, verify, execute, credentials = (payload.get(name) for name in ("request", "verify", "execute", "credentials"))
    if not all(isinstance(item, dict) for item in (request, verify, execute, credentials)):
        raise ValueError("invalid_request")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id):
        raise ValueError("invalid_request_id")
    if request.get("operation") != "cloudpress_totp_recovery" or request.get("risk") != "high":
        raise ValueError("invalid_operation")
    summary = request.get("summary")
    if not isinstance(summary, dict) or summary.get("operation") != "recover_account":
        raise ValueError("invalid_summary")
    expected_prefix = f"/api/totp-recovery/{request_id}/"
    for name, suffix in (("url", "verify"),):
        parsed = urlparse(verify.get(name) if isinstance(verify.get(name), str) else "")
        if f"{parsed.scheme}://{parsed.netloc}" != cloudpress_origin or parsed.path != expected_prefix + suffix or parsed.query or parsed.fragment:
            raise ValueError("invalid_verify_url")
    parsed = urlparse(execute.get("url") if isinstance(execute.get("url"), str) else "")
    if f"{parsed.scheme}://{parsed.netloc}" != cloudpress_origin or parsed.path != expected_prefix + "complete" or parsed.query or parsed.fragment:
        raise ValueError("invalid_execute_url")
    token = verify.get("token")
    password = credentials.get("new_password")
    totp = credentials.get("totp_code", "")
    backup = credentials.get("recovery_code", "")
    if not isinstance(token, str) or not 1 <= len(token) <= 128 or not isinstance(password, str) or len(password) < 10:
        raise ValueError("invalid_credentials")
    if (bool(totp) == bool(backup)) or (totp and (not isinstance(totp, str) or not re.fullmatch(r"\d{6}", totp))) or (backup and not isinstance(backup, str)):
        raise ValueError("invalid_authenticator_code")
    try:
        expires = datetime.fromisoformat(str(request["expires_at"]).replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("invalid_expiry") from error
    seconds = int((expires - datetime.now(timezone.utc)).total_seconds())
    if not 1 <= seconds <= 300:
        raise ValueError("expired_or_invalid_expiry")
    values = {"summary": json.dumps(summary, ensure_ascii=False, sort_keys=True), "verify_url": verify["url"], "execute_url": execute["url"], "recovery_token": token, "new_password": password}
    values["totp_code" if totp else "recovery_code"] = totp or backup
    ticket = LSFARequest("cloudpress_totp_recovery", "Verificar el autenticador y restablecer exclusivamente la contraseña solicitada.", RECOVERY_FIELDS, {"preflight": "totp_verified"}, seconds, risk=RiskLevel.HIGH, request_id=request_id, initiator="user", presentation="terminal")
    return ticket, values


def verified_receipt(verifier, context, method):
    """Obtiene un recibo sólo desde el verificador local confiable.

    El verificador recibe el resumen canónico, el método exigido y el binding
    opaco de esta confirmación. Debe autenticar a la persona localmente y
    devolver VerifiedConfirmation con esos mismos binding, method y expiry.
    Un booleano nunca es evidencia suficiente.
    """
    return verifier(json.loads(context.values["summary"]), method,
                    context.binding, context.expires_at)


def build_broker(cloudpress_origin: str, verifier, store_path: Path) -> TerminalAdapter:
    """Crea una cadena LSFA fail-closed; verifier debe realizar PIN+TOTP reales."""
    def preflight(values):
        try:
            summary = json.loads(values["summary"])
            parsed = urlparse(values["execute_url"])
            return (summary.get("operation") in OPERATIONS and f"{parsed.scheme}://{parsed.netloc}" == cloudpress_origin and parsed.path.startswith("/api/admin/approvals/") and bool(values["execution_token"]))
        except (TypeError, ValueError, KeyError):
            return False

    def execute(values):
        request = Request(values["execute_url"], method="POST", headers={"x-cloudpress-approval-token": values["execution_token"], "content-type": "application/json"})
        with urlopen(request, timeout=15) as response:  # nosec B310: preflight validates exact origin
            result = json.loads(response.read().decode("utf-8"))
        if response.status != 200 or result.get("state") != "accepted":
            raise ValueError("execution_rejected")
        return {"executed": True}

    policy = OperationPolicy(FIELDS, "cloudpress_target", preflight, execute, minimum_risk=RiskLevel.IRREVERSIBLE, check_names=("executed",))

    def confirm(context, method):
        # The verifier sees the canonical summary, never the execution token.
        return verified_receipt(verifier, context, method)

    def verify_confirmation(proof, context, method):
        if not isinstance(proof, VerifiedConfirmation):
            return None
        return proof

    client = LocalClient({"cloudpress_irreversible_action": policy}, AuthorizationStore(store_path), verify_confirmation)
    return TerminalAdapter(lambda _request: None, confirm, client=client)


def build_recovery_broker(cloudpress_origin: str, verifier, store_path: Path) -> TerminalAdapter:
    """El OTP se verifica en CloudPress; LSFA exige después el PIN local."""
    def preflight(values):
        request = Request(values["verify_url"], method="POST", headers={"x-cloudpress-recovery-token": values["recovery_token"], "content-type": "application/json"}, data=json.dumps({"code": values.get("totp_code", ""), "recoveryCode": values.get("recovery_code", "")}).encode("utf-8"))
        with urlopen(request, timeout=15) as response:  # nosec B310: parser pins exact origin and path
            result = json.loads(response.read().decode("utf-8"))
        return response.status == 200 and result.get("state") == "verified"

    def execute(values):
        request = Request(values["execute_url"], method="POST", headers={"x-cloudpress-recovery-token": values["recovery_token"], "content-type": "application/json"}, data=json.dumps({"password": values["new_password"]}).encode("utf-8"))
        with urlopen(request, timeout=15) as response:  # nosec B310: parser pins exact origin and path
            result = json.loads(response.read().decode("utf-8"))
        if response.status != 200 or result.get("state") != "used":
            raise ValueError("execution_rejected")
        return {"recovered": True}

    policy = OperationPolicy(RECOVERY_FIELDS, "totp_verified", preflight, execute, minimum_risk=RiskLevel.HIGH, check_names=("recovered",))
    def confirm(context, method):
        return verified_receipt(verifier, context, method)
    def verify_confirmation(proof, context, method):
        if not isinstance(proof, VerifiedConfirmation):
            return None
        return proof
    client = LocalClient({"cloudpress_totp_recovery": policy}, AuthorizationStore(store_path), verify_confirmation)
    return TerminalAdapter(lambda _request: None, confirm, client=client)


def result_for(adapter: TerminalAdapter, request: LSFARequest, values: dict) -> dict:
    """Ejecuta el adaptador con valores ya validados, sin imprimir secretos."""
    # ThreadingHTTPServer can handle parallel browser requests. Do not mutate
    # adapter.collect: another request could otherwise receive these values.
    request_adapter = TerminalAdapter(lambda _request: dict(values), adapter.confirm,
                                      client=adapter.client)
    return request_adapter.run(adapter.client.issue(request)).result.to_dict()


def load_verifier(reference: str):
    module_name, separator, attribute = reference.partition(":")
    if not separator or not module_name or not attribute:
        raise ValueError("verifier must use module:function")
    verifier = getattr(importlib.import_module(module_name), attribute)
    if not callable(verifier):
        raise ValueError("verifier must be callable")
    return verifier


def make_handler(adapter: TerminalAdapter, recovery_adapter: TerminalAdapter, cloudpress_origin: str):
    class Handler(BaseHTTPRequestHandler):
        def send_cors(self):
            self.send_header("Access-Control-Allow-Origin", cloudpress_origin)
            self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Private-Network", "true")

        def respond(self, status, payload):
            self.send_response(status)
            self.send_cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if status != 204:
                self.wfile.write(json.dumps(payload).encode("utf-8"))

        def do_OPTIONS(self):  # noqa: N802
            if self.headers.get("Origin") != cloudpress_origin:
                self.send_error(403)
                return
            self.respond(204, {})

        def do_GET(self):  # noqa: N802
            if self.path != "/health" or self.headers.get("Origin") != cloudpress_origin:
                self.respond(404, {"error_code": "not_found"})
                return
            self.respond(200, {"ok": True})

        def do_POST(self):  # noqa: N802
            if self.path not in {"/v1/cloudpress/approvals", "/v1/cloudpress/totp-recovery"} or self.headers.get("Origin") != cloudpress_origin:
                self.respond(403, {"status": "failed", "operation": "cloudpress_irreversible_action", "error_code": "invalid_origin"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16384:
                    raise ValueError("invalid_length")
                payload = json.loads(self.rfile.read(length))
                parser, selected = (parse_cloudpress_payload, adapter) if self.path == "/v1/cloudpress/approvals" else (parse_recovery_payload, recovery_adapter)
                request, values = parser(payload, cloudpress_origin)
                self.respond(200, result_for(selected, request, values))
            except Exception:
                self.respond(400, {"status": "failed", "operation": "cloudpress_irreversible_action", "error_code": "request_failed"})

        def log_message(self, _format, *_args):
            return  # never log bodies that contain a capability token

    return Handler


def main():
    parser = argparse.ArgumentParser(description="LSFA loopback companion for CloudPress")
    parser.add_argument("--origin", required=True, help="Exact CloudPress origin, e.g. https://cms.example")
    parser.add_argument("--verifier", required=True, help="Trusted local verifier as module:function")
    parser.add_argument("--store", default="cloudpress-lsfa-authorizations.sqlite3")
    args = parser.parse_args()
    origin = args.origin.rstrip("/")
    parsed = urlparse(origin)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path:
        raise SystemExit("--origin must be an exact HTTPS origin without a path")
    verifier = load_verifier(args.verifier)
    adapter = build_broker(origin, verifier, Path(args.store))
    recovery_adapter = build_recovery_broker(origin, verifier, Path(args.store))
    ThreadingHTTPServer(("127.0.0.1", 9463), make_handler(adapter, recovery_adapter, origin)).serve_forever()


if __name__ == "__main__":
    main()
