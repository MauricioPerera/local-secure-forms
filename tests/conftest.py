"""All authentication and effects below are synthetic test doubles, not MFA."""
import pytest
from src.lsfa import (AuthorizationStore, FieldSpec, GuiAdapter, LSFARequest,
                     LocalClient, OperationPolicy, VerifiedConfirmation)


@pytest.fixture
def harness(tmp_path):
    counter = 0

    def make(*, operation='connect_email', risk='low', floor='low', collect=None,
             confirm=None, execute=None, preflight=None, verifier=None, mode=GuiAdapter,
             ttl=60):
        nonlocal counter
        counter += 1
        clock = [100.0]
        effects = []
        proof = object()
        fields = (FieldSpec('password', 'secret', 'secret', True),)
        policy = OperationPolicy(fields, 'auth', preflight or (lambda v: True),
            execute or (lambda v: effects.append(v) or {'verified': True}),
            floor, ('verified',))

        def verify(receipt, context, method):
            if receipt is not proof:
                return None
            return VerifiedConfirmation(context.binding, method, context.expires_at)

        client = LocalClient({operation: policy},
            AuthorizationStore(tmp_path / f'auth-{counter}.sqlite'),
            verifier or verify, clock=lambda: clock[0])
        ticket = client.issue(LSFARequest(operation, 'Synthetic', fields,
            {'preflight': 'auth'}, ttl, risk=risk, request_id=f'test-{counter}'))
        adapter = mode(collect or (lambda r: {'password': 'SYNTHETIC_SENTINEL'}),
                       confirm or (lambda c, m: proof), client=client)
        return client, ticket, adapter, effects, clock

    return make
