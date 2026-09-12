import sqlite3
from src.lsfa import AuthorizationStore, LocalClient


def test_durable_content_binding_without_plaintext(harness):
    client, ticket, adapter, _, _ = harness()
    seen = []
    original = adapter.confirm
    def confirm(context, method):
        seen.append(context.binding)
        return original(context, method)
    adapter.confirm = confirm
    assert adapter.run(ticket).result.status == 'accepted'
    with sqlite3.connect(client.store.path) as connection:
        row = connection.execute('SELECT binding FROM execution_bindings').fetchone()
        dump = '\n'.join(connection.iterdump())
    assert row == (seen[0],)
    assert row[0] != ticket.binding
    assert 'SYNTHETIC_SENTINEL' not in dump
    # A restarted coordinator cannot renew or execute a previously used ID.
    restarted = LocalClient(client.policies, AuthorizationStore(client.store.path),
                            client.verify_confirmation, clock=client.clock)
    import pytest
    with pytest.raises(Exception, match='request_already_issued'):
        restarted.issue(ticket.request)


def test_binding_changes_with_identity_destination_scope_and_content(harness):
    client, ticket, _, _, _ = harness()
    from dataclasses import replace
    initial = client.context(ticket, {'to': 'a@example.test', 'scope': 'one', 'body': 'A'}).binding
    for values in [
        {'to': 'b@example.test', 'scope': 'one', 'body': 'A'},
        {'to': 'a@example.test', 'scope': 'two', 'body': 'A'},
        {'to': 'a@example.test', 'scope': 'one', 'body': 'B'},
    ]:
        assert client.context(ticket, values).binding != initial
    changed = replace(ticket.request, request_id='other')
    assert client.request_binding(changed, ticket.issued_at, ticket.expires_at) != ticket.binding
