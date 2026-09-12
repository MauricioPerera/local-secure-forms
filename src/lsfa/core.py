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
        if not isinstance(self.name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,63}", self.name):
            raise ValueError("field name invalid")
        if self.sensitivity not in {"public", "private", "secret"}:
            raise ValueError("field sensitivity invalid")
        if self.type not in {"text", "multiline", "email", "email_list", "hostname",
                             "integer", "boolean", "secret", "opaque_reference", "safe_local_path"}:
            raise ValueError("field type invalid")
        if type(self.required) is not bool:
            raise ValueError("required must be boolean")
        if self.type == "secret" and self.sensitivity != "secret":
            raise ValueError("secret sensitivity required")


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
        if (not isinstance(self.operation, str) or
                not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", self.operation) or
                not isinstance(self.purpose, str) or not self.purpose.strip() or
                len(self.purpose) > 4096 or not isinstance(self.fields, tuple) or
                not 1 <= len(self.fields) <= 64 or
                any(not isinstance(field, FieldSpec) for field in self.fields)):
            raise ValueError("request metadata or fields missing")
        if len({field.name for field in self.fields}) != len(self.fields):
            raise ValueError("duplicate fields")
        if type(self.expires_in_seconds) is not int or not 0 < self.expires_in_seconds <= 86400:
            raise ValueError("expiration invalid")
        RiskLevel(self.risk)
        if self.request_id is not None and (not isinstance(self.request_id, str) or
                not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", self.request_id)):
            raise ValueError("request id invalid")
        if (type(self.validation) is not dict or
                not set(self.validation) <= {"preflight", "on_failure"} or
                not isinstance(self.validation.get("preflight"), str) or
                not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", self.validation["preflight"]) or
                self.validation.get("on_failure", "do_not_store") != "do_not_store"):
            raise ValueError("validation invalid")
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
        if not isinstance(self.operation, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', self.operation):
            raise ValueError('invalid_operation')
        if self.request_id is not None and (not isinstance(self.request_id, str) or
                not re.fullmatch(r'[A-Za-z0-9._-]{1,128}', self.request_id)):
            raise ValueError('invalid_request_id')
        if self.risk is not None:
            RiskLevel(self.risk)
        if self.error_code is not None and (not isinstance(self.error_code, str) or
                not re.fullmatch(r'[a-z0-9_.-]{1,64}', self.error_code)):
            raise ValueError('invalid_error_code')
        for mapping in (self.checks, self.stored_refs):
            if mapping is not None and not isinstance(mapping, dict):
                raise ValueError("result metadata must be objects")
        self._validate_output()

    def _validate_output(self):
        # Only existence states and boolean checks cross the result boundary.
        # Arbitrary references require a trusted resolver, not raw strings.
        for key, value in (self.checks or {}).items():
            if not isinstance(key, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', key):
                raise ValueError('invalid check name')
            if type(value) is not bool:
                raise ValueError('checks require boolean states')
        for key, value in (self.stored_refs or {}).items():
            if not isinstance(key, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', key):
                raise ValueError('invalid reference name')
            if type(value) is not bool and value not in ('present', 'absent'):
                raise ValueError('references require existence states')

    def to_dict(self):
        self._validate_output()
        result = {"status": self.status, "operation": self.operation}
        for name in ("request_id", "risk", "checks", "stored_refs", "error_code"):
            value = getattr(self, name)
            if value is not None:
                result[name] = (value.value if isinstance(value, Enum) else
                                dict(value) if isinstance(value, dict) else value)
        return result
