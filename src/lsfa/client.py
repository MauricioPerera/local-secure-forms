"""Trusted local coordination. This module is not an OS security sandbox."""
from dataclasses import asdict, dataclass, replace
from copy import deepcopy
import hashlib
import hmac
import json
import re
import secrets
import time
from types import MappingProxyType
from uuid import uuid4

from .core import ConfirmationPolicy, FieldSpec, LSFARequest, RiskLevel


@dataclass(frozen=True)
class OperationPolicy:
    """Client-installed policy, never loaded from an agent request.

    Preflight may authenticate/check resources, but must not persist secrets or
    perform the requested effect. Execute alone performs the approved effect.
    """
    fields: tuple[FieldSpec, ...]
    preflight_name: str
    preflight: object
    execute: object
    minimum_risk: RiskLevel = RiskLevel.MEDIUM
    check_names: tuple[str, ...] = ()

    def __post_init__(self):
        LSFARequest('policy', 'Policy', self.fields,
                    {'preflight': self.preflight_name}, 1, risk=self.minimum_risk)
        if not callable(self.preflight) or not callable(self.execute):
            raise ValueError('policy_callbacks_required')
        if (type(self.check_names) is not tuple or len(set(self.check_names)) != len(self.check_names)
                or any(not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', name)
                       for name in self.check_names)):
            raise ValueError('invalid_check_names')


@dataclass(frozen=True)
class IssuedRequest:
    request: LSFARequest
    issued_at: float
    expires_at: float
    binding: str


@dataclass(frozen=True)
class ConfirmationContext:
    """UI-only data: never print/return this object to an agent.

    Show operation, purpose and effect-relevant values (mask secrets).
    Binding covers even masked values, including recipients, paths and body.
    """
    request: LSFARequest
    values: dict
    binding: str
    expires_at: float


@dataclass(frozen=True)
class VerifiedConfirmation:
    """Returned by the trusted verifier AFTER actual authentication.

    Not a bearer token and not proof merely because this class was constructed.
    The verifier must check a local authenticated UI receipt and actual factors
    where required. Never deserialize agent JSON into this object.
    """
    binding: str
    method: str
    expires_at: float


class LocalClient:
    def __init__(self, policies, store, verify_confirmation, *, clock=time.time):
        if not policies or not callable(verify_confirmation) or not callable(clock):
            raise ValueError('client_configuration_invalid')
        for name, policy in policies.items():
            if not isinstance(policy, OperationPolicy):
                raise ValueError('invalid_policy')
            if name == 'purge' and RiskLevel(policy.minimum_risk) != RiskLevel.IRREVERSIBLE:
                raise ValueError('purge_requires_irreversible')
        self.policies = MappingProxyType(dict(policies))
        self.store = store
        self.verify_confirmation = verify_confirmation
        self.clock = clock
        self._key = secrets.token_bytes(32)

    def digest(self, value):
        payload = json.dumps(value, sort_keys=True, separators=(',', ':'),
                             ensure_ascii=True, allow_nan=False).encode('utf-8')
        return hmac.new(self._key, payload, hashlib.sha256).hexdigest()

    def request_binding(self, request, issued_at, expires_at):
        return self.digest({'request': asdict(request), 'issued_at': issued_at,
                            'expires_at': expires_at})

    def issue(self, request):
        request = replace(deepcopy(request))
        policy = self.policies.get(request.operation)
        if policy is None:
            raise ValueError('unknown_operation')
        if request.operation == 'purge' and RiskLevel(request.risk) != RiskLevel.IRREVERSIBLE:
            raise ValueError('purge_requires_irreversible')
        if request.fields != policy.fields or request.validation['preflight'] != policy.preflight_name:
            raise ValueError('request_policy_mismatch')
        levels = list(RiskLevel)
        risk = max((RiskLevel(request.risk), RiskLevel(policy.minimum_risk)), key=levels.index)
        request = replace(request, risk=risk, request_id=request.request_id or uuid4().hex)
        issued = self.clock()
        expires = issued + request.expires_in_seconds
        binding = self.request_binding(request, issued, expires)
        self.store.issue(request.request_id, binding, expires, issued)
        return IssuedRequest(request, issued, expires, binding)

    def validate_ticket(self, ticket):
        if not isinstance(ticket, IssuedRequest):
            raise ValueError('issued_request_required')
        expected = self.request_binding(ticket.request, ticket.issued_at, ticket.expires_at)
        if not hmac.compare_digest(expected, ticket.binding):
            raise ValueError('request_changed')
        if self.store.status(ticket.request.request_id) != 'pending':
            raise ValueError('authorization_unavailable')
        now = self.clock()
        if now < ticket.issued_at or now >= ticket.expires_at:
            raise TimeoutError('expired')
        return self.policies[ticket.request.operation]

    def context(self, ticket, values):
        return ConfirmationContext(deepcopy(ticket.request), deepcopy(values),
            self.digest({'ticket': ticket.binding, 'values': values}), ticket.expires_at)

    def verify(self, proof, context, method):
        evidence = self.verify_confirmation(proof, deepcopy(context), method)
        if not isinstance(evidence, VerifiedConfirmation):
            raise ValueError('confirmation_unverified')
        ConfirmationPolicy.validate(context.request.risk, evidence.method)
        if (not hmac.compare_digest(evidence.binding, context.binding) or
                type(evidence.expires_at) not in (int, float) or
                not self.clock() < evidence.expires_at <= context.expires_at):
            raise ValueError('confirmation_unverified')
        return evidence.expires_at
