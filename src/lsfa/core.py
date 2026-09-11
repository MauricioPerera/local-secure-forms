"""Modelos y reglas portables del protocolo LSFA."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    IRREVERSIBLE = "irreversible"


class ConfirmationPolicy:
    """Regla de confirmación mínima; no captura PIN ni códigos."""

    METHODS = {"user_accept", "pin", "pin_and_totp"}

    @staticmethod
    def minimum_for(risk):
        level = RiskLevel(risk)
        return {
            RiskLevel.LOW: "user_accept",
            RiskLevel.MEDIUM: "user_accept",
            RiskLevel.HIGH: "pin",
            RiskLevel.IRREVERSIBLE: "pin_and_totp",
        }[level]

    @classmethod
    def validate(cls, risk, method):
        if method not in cls.METHODS:
            raise ValueError("confirmation method invalid")
        required = cls.minimum_for(risk)
        rank = {"user_accept": 0, "pin": 1, "pin_and_totp": 2}
        if rank[method] < rank[required]:
            raise ValueError("confirmation method is too weak for risk")


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: str
    sensitivity: str
    required: bool = False

    def __post_init__(self):
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,63}", self.name):
            raise ValueError("field name invalid")
        if self.sensitivity not in {"public", "private", "secret"}:
            raise ValueError("field sensitivity invalid")


@dataclass(frozen=True)
class LSFARequest:
    operation: str
    purpose: str
    fields: tuple[FieldSpec, ...]
    validation: dict
    expires_in_seconds: int
    risk: RiskLevel = RiskLevel.MEDIUM
    request_id: str | None = None
    initiator: str = "agent"

    def __post_init__(self):
        if not self.operation or not self.purpose or not self.fields:
            raise ValueError("request metadata or fields missing")
        if not isinstance(self.expires_in_seconds, int) or not 0 < self.expires_in_seconds <= 86400:
            raise ValueError("expiration invalid")
        if self.initiator not in {"user", "agent", "system"}:
            raise ValueError("initiator invalid")

    def expired(self, created_at, now=None):
        current = now or datetime.now(timezone.utc)
        return (current - created_at).total_seconds() >= self.expires_in_seconds


@dataclass(frozen=True)
class LSFAResult:
    status: str
    operation: str
    request_id: str | None = None
    risk: RiskLevel | None = None
    checks: dict | None = None
    stored_refs: dict | None = None
    error_code: str | None = None

    def __post_init__(self):
        if self.status not in {"accepted", "declined", "cancelled", "invalid", "failed", "expired"}:
            raise ValueError("result status invalid")
        for mapping in (self.checks, self.stored_refs):
            if mapping is not None and not isinstance(mapping, dict):
                raise ValueError("result metadata must be objects")

    def to_dict(self):
        result = {"status": self.status, "operation": self.operation}
        for name in ("request_id", "risk", "checks", "stored_refs", "error_code"):
            value = getattr(self, name)
            if value is not None:
                result[name] = value.value if isinstance(value, Enum) else value
        return result
