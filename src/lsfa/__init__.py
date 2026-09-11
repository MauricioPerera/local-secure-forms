"""SDK de referencia mínimo para LSFA 0.2."""

from .core import (
    ConfirmationPolicy,
    FieldSpec,
    LSFARequest,
    LSFAResult,
    RiskLevel,
)
from .adapters import GuiAdapter, ManualAdapter, PresentationResult, TerminalAdapter

__all__ = [
    "ConfirmationPolicy",
    "FieldSpec",
    "LSFARequest",
    "LSFAResult",
    "RiskLevel",
    "GuiAdapter",
    "ManualAdapter",
    "PresentationResult",
    "TerminalAdapter",
]
