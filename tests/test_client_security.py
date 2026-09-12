"""Client policy, expiry, bound confirmation, redaction and replay behavior."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import pytest
from src.lsfa import VerifiedConfirmation, GuiAdapter, TerminalAdapter, ManualAdapter


@pytest.mark.parametrize('stage', ['before', 'collect', 'preflight', 'confirm', 'verify'])
def test_expiry_at_every_boundary(harness, stage):
    client, ticket, adapter, effects, clock = harness(ttl=1)
    def expire(callback):
        def wrapped(*args):
            result = callback(*args)
            clock[0] += 1
            return result
        return wrapped
    if stage == 'before':
        clock[0] += 1
        adapter.collect = lambda r: pytest.fail('expired request collected')
    elif stage == 'collect':
        adapter.collect = expire(adapter.collect)
    elif stage == 'confirm':
        adapter.confirm = expire(adapter.confirm)
    elif stage == 'verify':
        client.verify_confirmation = expire(client.verify_confirmation)
    else:
        # Controlled test instrumentation of the trusted preflight callback.
        object.__setattr__(client.policies['connect_email'], 'preflight', expire(lambda v: True))
    assert adapter.run(ticket).result.status in ('expired', 'failed')
    assert effects == []


def test_replay_and_concurrent_effects(harness):
    client, ticket, adapter, effects, _ = harness()
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: adapter.run(ticket), range(16)))
    assert sum(r.result.status == 'accepted' for r in results) == 1
    assert len(effects) == 1
    assert adapter.run(ticket).result.status == 'failed'
    with pytest.raises(Exception, match='request_already_issued'):
        client.issue(ticket.request)


@pytest.mark.parametrize('risk', ['low', 'medium', 'high', 'irreversible'])
def test_purge_floor_and_legitimate_confirmation(harness, risk):
    if risk != 'irreversible':
        with pytest.raises(ValueError, match='purge_requires_irreversible'):
            harness(operation='purge', risk=risk, floor='irreversible')
        return
    _, ticket, adapter, effects, _ = harness(operation='purge', risk=risk, floor='irreversible')
    assert ticket.request.risk == 'irreversible'
    assert adapter.run(ticket).result.status == 'accepted'
    assert len(effects) == 1


@pytest.mark.parametrize('proof', [True, 'pin_and_totp', {'method': 'pin_and_totp'}])
def test_method_name_is_not_authentication(harness, proof):
    _, ticket, adapter, effects, _ = harness(operation='purge', risk='irreversible', floor='irreversible',
                                          confirm=lambda c, m: proof)
    assert adapter.run(ticket).result.status == 'failed'
    assert not effects


@pytest.mark.parametrize('fault', ['binding', 'method', 'expiry', 'boolean_expiry'])
def test_verifier_evidence_is_bound_and_fresh(harness, fault):
    def verifier(proof, context, method):
        return VerifiedConfirmation('0'*64 if fault == 'binding' else context.binding,
            'user_accept' if fault == 'method' else method,
            True if fault == 'boolean_expiry' else 100 if fault == 'expiry' else context.expires_at)
    _, ticket, adapter, effects, _ = harness(risk='high', verifier=verifier)
    assert adapter.run(ticket).result.status == 'failed'
    assert not effects


def test_mutated_ticket_rejected_and_ui_cannot_change_effect(harness):
    _, ticket, adapter, effects, _ = harness()
    changed = replace(ticket, request=replace(ticket.request, purpose='Changed'))
    assert adapter.run(changed).result.status == 'failed'
    original = adapter.confirm
    def confirm(context, method):
        context.values['password'] = 'UI_MUTATION'
        return original(context, method)
    adapter.confirm = confirm
    assert adapter.run(ticket).result.status == 'accepted'
    assert effects == [{'password': 'SYNTHETIC_SENTINEL'}]


def test_unknown_operation_validator_and_policy_mismatch(harness):
    client, ticket, _, effects, _ = harness()
    for changed in [replace(ticket.request, operation='unregistered'),
                    replace(ticket.request, validation={'preflight': 'unregistered'}),
                    replace(ticket.request, fields=(replace(ticket.request.fields[0], required=False),))]:
        with pytest.raises(ValueError):
            client.issue(changed)
    assert not effects


def test_preflight_failure_prevents_execution(harness):
    _, ticket, adapter, effects, _ = harness(preflight=lambda v: False)
    assert adapter.run(ticket).result.error_code == 'preflight_failed'
    assert not effects


@pytest.mark.parametrize('mode', [GuiAdapter, TerminalAdapter, ManualAdapter])
def test_every_adapter_rejects_unverified_irreversible_action(harness, mode):
    _, ticket, adapter, effects, _ = harness(operation='purge', risk='irreversible', floor='irreversible',
                                          mode=mode, confirm=lambda c, m: True)
    assert adapter.run(ticket).result.status == 'failed'
    assert not effects


@pytest.mark.parametrize('operation', ['soft_delete', 'restore'])
def test_reversible_operations_are_separate_and_do_not_require_purge_factors(harness, operation):
    _, ticket, adapter, effects, _ = harness(operation=operation)
    methods = []
    original = adapter.confirm
    adapter.confirm = lambda c, m: methods.append(m) or original(c, m)
    assert adapter.run(ticket).result.status == 'accepted'
    assert methods == ['user_accept'] and len(effects) == 1


def test_proof_expiring_after_verification_is_not_executed(harness):
    client, ticket, adapter, effects, clock = harness()
    original = client.verify
    def verify(*args):
        original(*args)
        # Evidence deadline ends before the later ticket-consumption boundary.
        clock[0] = 101
        return 101
    client.verify = verify
    assert adapter.run(ticket).result.status == 'expired'
    assert not effects


def test_client_cannot_register_weak_purge(harness):
    with pytest.raises(ValueError, match='purge_requires_irreversible'):
        harness(operation='purge', floor='high')


@pytest.mark.parametrize('stage', ['collect', 'confirm', 'execute', 'preflight', 'verify'])
def test_callback_exceptions_do_not_leak(harness, stage, capsys, caplog):
    def fail(*args):
        raise RuntimeError('SYNTHETIC_SENTINEL')
    kwargs = {'verifier' if stage == 'verify' else stage: fail}
    _, ticket, adapter, _, _ = harness(**kwargs)
    result = adapter.run(ticket)
    captured = capsys.readouterr()
    assert result.result.status == 'failed'
    assert 'SYNTHETIC_SENTINEL' not in json.dumps(result.result.to_dict()) + captured.out + captured.err + caplog.text


@pytest.mark.parametrize('output', [
    {'verified': 'SYNTHETIC_SENTINEL'}, {'verified': {'nested': 'SYNTHETIC_SENTINEL'}},
    {'SYNTHETIC_SENTINEL': True}, {'other': True}, None, ['SYNTHETIC_SENTINEL'],
])
def test_output_allowlist_and_unknown_effect_prevent_retry(harness, output):
    effects = []
    client, ticket, adapter, _, _ = harness(execute=lambda v: effects.append(1) or output)
    result = adapter.run(ticket)
    assert result.result.status == 'failed' and result.values_consumed
    assert 'SYNTHETIC_SENTINEL' not in json.dumps(result.result.to_dict())
    assert client.store.status(ticket.request.request_id) == 'unknown'
    adapter.run(ticket)
    assert effects == [1]
