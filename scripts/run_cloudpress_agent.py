"""Persistent, least-privilege runner for CloudPress agent tasks.

The runner never receives the CloudPress bearer.  It talks only to the local
LSFA companion, which reads that bearer from the OS credential store and
enforces its route/action allowlist.  CloudPress in turn binds every business
request to the claimed task step.

This is deliberately a deterministic executor, not an implicit model client:
plans supply a bounded request per step.  A model provider can prepare those
plans only through the separately governed runtime/catalogue flow.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

import keyring


DEFAULT_ORIGIN = "https://auth-free-test-20260915.pages.dev"
DEFAULT_LOOPBACK = "http://127.0.0.1:9463/v1/cloudpress/agent-api"
CAPABILITY_SERVICE = "lsfa.cloudpress.agent-capability"
READ_RESOURCES = {
    "content": "/api/admin/entries",
    "users": "/api/admin/users",
    "taxonomies": "/api/admin/taxonomies",
    "menus": "/api/admin/menus",
    "plugins": "/api/admin/plugins",
    "media": "/api/admin/media",
    "blocks": "/api/admin/blocks",
}


class RunnerError(RuntimeError):
    """A non-secret, operator-safe execution error."""


@dataclass(frozen=True)
class AgentRequest:
    path: str
    method: str
    body: dict[str, Any] | None = None


def stored_channel(origin: str) -> str:
    try:
        value = json.loads(keyring.get_password(CAPABILITY_SERVICE, origin) or "")
        channel = value.get("channel_token")
    except Exception as error:  # nosec B110: credential parsing is fail-closed
        raise RunnerError("No hay una capacidad LSFA local disponible.") from error
    if not isinstance(channel, str) or not channel:
        raise RunnerError("No hay un canal LSFA local disponible.")
    return channel


class Companion:
    def __init__(self, origin: str, loopback: str = DEFAULT_LOOPBACK):
        self.origin, self.loopback = origin, loopback.rstrip("/")

    def call(self, request: AgentRequest, execution: dict[str, Any] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "protocol": "lsfa", "version": "0.2", "origin": self.origin,
            "request": {"path": request.path, "method": request.method, "body": request.body},
        }
        if execution is not None:
            payload["request"]["execution"] = execution
        remote = urllib.request.Request(
            self.loopback, data=json.dumps(payload).encode("utf-8"), method="POST",
            headers={"Origin": self.origin, "Content-Type": "application/json", "X-LSFA-Channel-Token": stored_channel(self.origin)},
        )
        try:
            with urllib.request.urlopen(remote, timeout=30) as response:
                result = json.load(response)
        except Exception as error:  # never include transport bodies/tokens in an agent trace
            raise RunnerError("El companion LSFA no respondió.") from error
        status, body = result.get("status"), result.get("body")
        if not isinstance(status, int) or not 200 <= status < 300 or not isinstance(body, dict):
            raise RunnerError("El companion rechazó la operación.")
        if isinstance(body.get("status"), int) and body["status"] >= 400:
            raise RunnerError(f"CloudPress rechazó {request.method} {request.path}.")
        return body

    def runtime(self, action: str, **values: Any) -> dict[str, Any]:
        return self.call(AgentRequest("/api/admin/agent-runtime", "POST", {"action": action, **values}))

    def execution(self, action: str, task_id: str, ordinal: int, **values: Any) -> dict[str, Any]:
        return self.call(AgentRequest("/api/admin/agent-execution", "POST", {"action": action, "taskId": task_id, "ordinal": ordinal, **values}))


def bounded_request(step: dict[str, Any]) -> AgentRequest:
    """Translate only a declared plan input; do not invent administrative calls."""
    tool, supplied = step.get("tool"), step.get("input") or {}
    if not isinstance(supplied, dict):
        raise RunnerError("La entrada del paso no es válida.")
    if tool == "cloudpress_read_admin_state" and not supplied:
        resource = (step.get("expected") or {}).get("resource", "content")
        path = READ_RESOURCES.get(resource)
        if path:
            return AgentRequest(path, "GET")
    request = supplied.get("request")
    if not isinstance(request, dict):
        raise RunnerError("El paso requiere una solicitud declarada en su plan.")
    path, method, body = request.get("path"), request.get("method"), request.get("body")
    if not isinstance(path, str) or not path.startswith("/api/admin/") or "//" in path or "#" in path:
        raise RunnerError("La ruta declarada del paso no es válida.")
    if method not in {"GET", "POST", "PATCH", "PUT", "DELETE"} or (body is not None and not isinstance(body, dict)):
        raise RunnerError("El método o cuerpo declarado del paso no es válido.")
    return AgentRequest(path, method, body)


def safe_result(value: dict[str, Any]) -> dict[str, Any]:
    """Return only identifiers/state needed for CloudPress server postconditions."""
    result = {key: value[key] for key in ("id", "key", "status", "active", "scope", "value") if key in value}
    if not result:
        for collection in ("items", "users", "terms", "menus", "plugins"):
            if isinstance(value.get(collection), list):
                return {"resource": collection, "count": len(value[collection])}
        result = {"accepted": True}
    return result


def execute_assignment(companion: Companion, assignment: dict[str, Any]) -> dict[str, Any]:
    job, context = assignment.get("job"), assignment.get("context")
    if not isinstance(job, dict) or not isinstance(context, dict):
        raise RunnerError("La asignación del runtime no es válida.")
    task_id, lease_id = job.get("taskId"), job.get("leaseId")
    plan = context.get("plan")
    if not isinstance(task_id, str) or not isinstance(lease_id, str) or not isinstance(plan, list):
        raise RunnerError("La asignación no contiene tarea, lease y plan válidos.")
    completed = 0
    for ordinal, step in enumerate(plan, start=1):
        if not isinstance(step, dict):
            raise RunnerError("El plan contiene un paso inválido.")
        started = companion.execution("start_step", task_id, ordinal).get("step", {})
        if started.get("state") == "waiting_approval":
            companion.runtime("checkpoint", jobId=job["id"], leaseId=lease_id, checkpoint={"phase": "waiting_approval", "ordinal": ordinal})
            return {"state": "waiting_approval", "taskId": task_id, "ordinal": ordinal}
        if started.get("state") != "running":
            raise RunnerError("CloudPress no inició el paso reclamado.")
        execution = {"taskId": task_id, "ordinal": ordinal}
        try:
            response = companion.call(bounded_request(step), execution)
            outcome = {"result": safe_result(response), "verification": {"verified": True, "evidenceLevel": "agent-attested"}}
            # Persist the bounded checkpoint before finishing the final step:
            # finish_step may atomically complete the task and release the
            # runtime lease, after which another checkpoint must be rejected.
            companion.runtime("checkpoint", jobId=job["id"], leaseId=lease_id, checkpoint={"phase": "tool_executed", "ordinal": ordinal})
            companion.execution("finish_step", task_id, ordinal, outcome=outcome)
            completed += 1
        except RunnerError as error:
            companion.execution("fail_step", task_id, ordinal, error=str(error)[:1000])
            return {"state": "failed", "taskId": task_id, "ordinal": ordinal}
    return {"state": "completed", "taskId": task_id, "steps": completed}


def run_once(companion: Companion) -> dict[str, Any]:
    assignment = companion.runtime("claim").get("assignment")
    return {"state": "idle"} if assignment is None else execute_assignment(companion, assignment)


def main() -> None:
    parser = argparse.ArgumentParser(description="Persistent local runner for governed CloudPress agent tasks")
    parser.add_argument("--origin", default=DEFAULT_ORIGIN)
    parser.add_argument("--loopback", default=DEFAULT_LOOPBACK)
    parser.add_argument("--interval", type=float, default=5.0)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    if not args.origin.startswith("https://") or args.origin.rstrip("/") != args.origin:
        raise SystemExit("--origin debe ser un origen HTTPS exacto.")
    if not 1 <= args.interval <= 300:
        raise SystemExit("--interval debe estar entre 1 y 300 segundos.")
    companion = Companion(args.origin, args.loopback)
    while True:
        try:
            result = run_once(companion)
            print(json.dumps(result, ensure_ascii=False))
        except RunnerError as error:
            print(json.dumps({"state": "error", "error": str(error)}, ensure_ascii=False))
        if args.once:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
