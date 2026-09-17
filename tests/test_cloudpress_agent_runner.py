import importlib.util
import sys
from pathlib import Path


RUNNER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_cloudpress_agent.py"
spec = importlib.util.spec_from_file_location("cloudpress_agent_runner", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = RUNNER
spec.loader.exec_module(RUNNER)


def test_read_step_has_a_bounded_default_route():
    request = RUNNER.bounded_request({"tool": "cloudpress_read_admin_state", "expected": {"resource": "users"}})
    assert request.path == "/api/admin/users"
    assert request.method == "GET"


def test_non_read_step_requires_declared_bounded_request():
    try:
        RUNNER.bounded_request({"tool": "cloudpress_create_draft", "input": {}})
    except RUNNER.RunnerError as error:
        assert "solicitud declarada" in str(error)
    else:
        raise AssertionError("El runner no debe inventar mutaciones administrativas.")


def test_runner_completes_one_task_scoped_step_without_bearer_access():
    calls = []

    class Companion:
        def execution(self, action, task_id, ordinal, **values):
            calls.append(("execution", action, task_id, ordinal, values))
            return {"step": {"state": "running"} if action == "start_step" else {"taskCompleted": True}}

        def call(self, request, execution=None):
            calls.append(("call", request.path, request.method, execution))
            return {"users": [{"id": 1}]}

        def runtime(self, action, **values):
            calls.append(("runtime", action, values))
            return {"checkpoint": {}}

    result = RUNNER.execute_assignment(Companion(), {"job": {"id": "job", "taskId": "00000000-0000-0000-0000-000000000000", "leaseId": "lease"}, "context": {"plan": [{"tool": "cloudpress_read_admin_state", "expected": {"resource": "users"}}]}})
    assert result == {"state": "completed", "taskId": "00000000-0000-0000-0000-000000000000", "steps": 1}
    assert ("call", "/api/admin/users", "GET", {"taskId": "00000000-0000-0000-0000-000000000000", "ordinal": 1}) in calls
    assert any(item[0:2] == ("runtime", "checkpoint") for item in calls)
    checkpoint = next(index for index, item in enumerate(calls) if item[0:2] == ("runtime", "checkpoint"))
    finish = next(index for index, item in enumerate(calls) if item[0:2] == ("execution", "finish_step"))
    assert checkpoint < finish, "El checkpoint debe preceder al cierre que libera el lease."


def test_runner_stops_when_cloudpress_requires_a2f():
    class Companion:
        def execution(self, action, *_args, **_values):
            return {"step": {"state": "waiting_approval"}}

        def runtime(self, action, **_values):
            assert action == "checkpoint"
            return {"checkpoint": {}}

    result = RUNNER.execute_assignment(Companion(), {"job": {"id": "job", "taskId": "00000000-0000-0000-0000-000000000000", "leaseId": "lease"}, "context": {"plan": [{"tool": "cloudpress_sensitive_action"}]}})
    assert result["state"] == "waiting_approval"
