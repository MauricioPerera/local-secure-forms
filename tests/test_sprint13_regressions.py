"""Original four audit reproductions, migrated to client-issued requests."""
import json


def test_executor_echo_cannot_escape_through_checks(harness):
    client, ticket, adapter, _, _ = harness(execute=lambda values: dict(values))
    result = adapter.run(ticket).result
    assert 'SYNTHETIC_SENTINEL' not in json.dumps(result.to_dict())
    assert result.status != 'accepted'
    assert client.store.status(ticket.request.request_id) == 'unknown'


def test_expiration_during_capture_prevents_execution(harness):
    client, ticket, adapter, effects, clock = harness(ttl=1)
    def collect(r):
        clock[0] += 1.05
        return {'password': 'synthetic'}
    adapter.collect = collect
    assert adapter.run(ticket).result.status == 'expired'
    assert effects == []


def test_purge_cannot_choose_basic_confirmation(harness):
    _, ticket, adapter, effects, _ = harness(operation='purge', floor='irreversible',
        confirm=lambda c, m: m == 'user_accept')
    result = adapter.run(ticket).result
    assert effects == []
    assert result.status != 'accepted'
    assert result.risk == 'irreversible'


def test_required_null_and_extra_fields_never_reach_executor(harness):
    _, ticket, adapter, effects, _ = harness(
        collect=lambda r: {'password': None, 'extra': 'unexpected'})
    assert adapter.run(ticket).result.status == 'invalid'
    assert effects == []
