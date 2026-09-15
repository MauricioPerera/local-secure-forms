"""SDK LSFA 0.2 con extensión declarativa de presentación 0.3."""

from .core import (
    ConfirmationPolicy,
    FieldSpec,
    LSFARequest,
    LSFAResult,
    PresentationSection,
    PresentationSpec,
    RiskLevel,
)
from .adapters import GuiAdapter, ManualAdapter, PresentationResult, TerminalAdapter
from .authorization import AuthorizationStore
from .client import LocalClient, OperationPolicy, VerifiedConfirmation
from .presentation import PresentationRegistry

__all__ = [
    "ConfirmationPolicy",
    "FieldSpec",
    "LSFARequest",
    "LSFAResult",
    "PresentationSection",
    "PresentationSpec",
    "PresentationRegistry",
    "RiskLevel",
    "GuiAdapter",
    "ManualAdapter",
    "PresentationResult",
    "TerminalAdapter",
    "AuthorizationStore",
    "LocalClient",
    "OperationPolicy",
    "VerifiedConfirmation",
]
