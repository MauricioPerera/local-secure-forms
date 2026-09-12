"""Presentation callbacks share a client-owned, fail-closed execution path."""
from copy import deepcopy
from dataclasses import dataclass

from .core import ConfirmationPolicy, LSFAResult
from .client import IssuedRequest
from .validation import validate_values


@dataclass(frozen=True)
class PresentationResult:
    result: LSFAResult
    values_consumed: bool = False


class PresentationAdapter:
    """Collect/confirm are trusted local callbacks, not implemented GUIs.

    Construct with client=LocalClient(...), then run client.issue(request).
    Executors belong to operation policies, not to the agent request.
    """
    mode = 'abstract'

    def __init__(self, collect, confirm, *, client):
        self.collect = collect
        self.confirm = confirm
        self.client = client

    def run(self, ticket: IssuedRequest):
        if not isinstance(ticket, IssuedRequest):
            raise ValueError('issued_request_required')
        ticket = deepcopy(ticket)
        request = ticket.request
        consumed = False

        def outcome(status, error=None, checks=None):
            return PresentationResult(LSFAResult(status, request.operation,
                request_id=request.request_id, risk=request.risk, checks=checks,
                error_code=error), consumed)

        try:
            policy = self.client.validate_ticket(ticket)
            values = self.collect(deepcopy(request))
            self.client.validate_ticket(ticket)
            if values is None:
                return outcome('cancelled')
            try:
                values = validate_values(policy.fields, values)
            except ValueError:
                return outcome('invalid', 'invalid_input')
            if policy.preflight(deepcopy(values)) is not True:
                return outcome('invalid', 'preflight_failed')
            self.client.validate_ticket(ticket)
            context = self.client.context(ticket, values)
            method = ConfirmationPolicy.minimum_for(request.risk)
            proof = self.confirm(deepcopy(context), method)
            self.client.validate_ticket(ticket)
            if proof is None or proof is False:
                return outcome('declined')
            proof_deadline = self.client.verify(proof, context, method)
            self.client.validate_ticket(ticket)
            now = self.client.clock()
            if now >= proof_deadline:
                raise TimeoutError('expired')
            self.client.store.consume(request.request_id, ticket.binding, now,
                                      execution_binding=context.binding)
            consumed = True
            try:
                checks = policy.execute(deepcopy(values))
                if (type(checks) is not dict or not set(checks) <= set(policy.check_names)
                        or any(type(value) is not bool for value in checks.values())):
                    raise ValueError('invalid_execution_result')
                result = outcome('accepted', checks=dict(checks))
            except Exception:
                self.client.store.finish(request.request_id, 'unknown')
                return outcome('failed', 'execution_outcome_unknown')
            self.client.store.finish(request.request_id, 'accepted')
            return result
        except TimeoutError:
            return outcome('expired', 'expired')
        except Exception:
            # Never expose callback exception text or tracebacks. Executing
            # rows remain locked even when durable finalization fails.
            return outcome('failed', 'execution_outcome_unknown' if consumed else 'request_failed')


class GuiAdapter(PresentationAdapter):
    mode = 'form'


class TerminalAdapter(PresentationAdapter):
    mode = 'terminal'


class ManualAdapter(PresentationAdapter):
    mode = 'manual'
