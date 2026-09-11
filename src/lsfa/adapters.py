"""Adaptadores de presentación de referencia sin dependencia de UI."""

from dataclasses import dataclass

from .core import ConfirmationPolicy, LSFARequest, LSFAResult


@dataclass(frozen=True)
class PresentationResult:
    result: LSFAResult
    values_consumed: bool = False


class PresentationAdapter:
    """Contrato común: la UI captura valores y el cliente ejecuta la acción."""

    mode = "abstract"

    def __init__(self, collect, confirm):
        self.collect = collect
        self.confirm = confirm

    def run(self, request: LSFARequest, execute):
        values = self.collect(request)
        if values is None:
            return PresentationResult(LSFAResult("cancelled", request.operation), False)
        if not isinstance(values, dict):
            return PresentationResult(LSFAResult("invalid", request.operation, error_code="invalid_input"), False)
        required = {field.name for field in request.fields if field.required}
        if not required <= values.keys():
            return PresentationResult(LSFAResult("invalid", request.operation, error_code="missing_field"), False)
        method = ConfirmationPolicy.minimum_for(request.risk)
        if not self.confirm(request, method):
            return PresentationResult(LSFAResult("declined", request.operation), False)
        try:
            checks = execute(values)
        except Exception:
            return PresentationResult(LSFAResult("failed", request.operation, error_code="execution_failed"), True)
        return PresentationResult(LSFAResult("accepted", request.operation, checks=checks or {}), True)


class GuiAdapter(PresentationAdapter):
    mode = "form"


class TerminalAdapter(PresentationAdapter):
    mode = "terminal"


class ManualAdapter(PresentationAdapter):
    mode = "manual"
