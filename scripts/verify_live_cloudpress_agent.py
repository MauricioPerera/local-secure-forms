"""Non-mutating live security verification for the CloudPress agent channel.

This verifier intentionally does *not* invoke business tools directly. An
agent capability is not an administrator session: CloudPress must reject every
business request until the runner has claimed a task and started its matching
step. Direct calls used by an earlier version of this script produced a 403
and were incorrectly described as an end-to-end tool test.

For a mutating end-to-end run, create a bounded task in CloudPress' Agents
console and let ``scripts/run_cloudpress_agent.py --once`` claim it. The
server then persists the task, step, postcondition and trace evidence.
"""

from __future__ import annotations

import json
import keyring
import urllib.request


ORIGIN = "https://auth-free-test-20260915.pages.dev"
LOOPBACK = "http://127.0.0.1:9463"
CAPABILITY_SERVICE = "lsfa.cloudpress.agent-capability"


def channel_token() -> str:
    try:
        stored = json.loads(keyring.get_password(CAPABILITY_SERVICE, ORIGIN) or "")
        token = stored.get("channel_token")
    except Exception as error:  # nosec B110: fail closed without credential details
        raise RuntimeError("No hay canal LSFA vinculado para esta prueba.") from error
    if not isinstance(token, str) or not token:
        raise RuntimeError("No hay canal LSFA vinculado para esta prueba.")
    return token


def call_agent(path: str) -> dict:
    payload = {
        "protocol": "lsfa", "version": "0.2", "origin": ORIGIN,
        "request": {"path": path, "method": "GET", "body": None},
    }
    request = urllib.request.Request(
        f"{LOOPBACK}/v1/cloudpress/agent-api",
        data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Origin": ORIGIN, "Content-Type": "application/json", "X-LSFA-Channel-Token": channel_token()},
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        result = json.load(response)
    if not isinstance(result, dict):
        raise RuntimeError("El companion no devolvió una respuesta válida.")
    return result


def health() -> None:
    request = urllib.request.Request(f"{LOOPBACK}/health", headers={"Origin": ORIGIN})
    with urllib.request.urlopen(request, timeout=10) as response:
        if response.status != 200 or json.load(response) != {"ok": True}:
            raise RuntimeError("El companion no superó la comprobación de salud.")


def main() -> None:
    health()
    # A bearer alone must never make an administrative read: no task id or
    # ordinal is sent through this request.
    response = call_agent("/api/admin/entries")
    body = response.get("body")
    if response.get("status") != 403 or not isinstance(body, dict) or not isinstance(body.get("code"), str):
        raise RuntimeError("CloudPress permitió una herramienta de negocio sin contexto de tarea.")
    print(json.dumps({
        "ok": True,
        "checks": ["companion-health", "agent-channel", "business-tool-requires-active-task-step"],
        "next": "Crea una tarea limitada en la consola de Agentes y ejecuta scripts/run_cloudpress_agent.py --once para una prueba E2E mutante.",
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
