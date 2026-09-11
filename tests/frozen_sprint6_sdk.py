"""Pruebas congeladas del SDK Python de referencia LSFA."""

from datetime import datetime, timedelta, timezone

import pytest

from src.lsfa import ConfirmationPolicy, FieldSpec, LSFARequest, LSFAResult, RiskLevel


def test_risk_policy_requires_stronger_confirmation():
    assert ConfirmationPolicy.minimum_for("low") == "user_accept"
    assert ConfirmationPolicy.minimum_for("high") == "pin"
    assert ConfirmationPolicy.minimum_for("irreversible") == "pin_and_totp"
    with pytest.raises(ValueError):
        ConfirmationPolicy.validate("irreversible", "pin")


def test_request_expiration_is_deterministic():
    request = LSFARequest("connect_email", "Configurar correo", (FieldSpec("password", "secret", "secret", True),), {"preflight": "auth"}, 60)
    created = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert request.expired(created, created + timedelta(seconds=59)) is False
    assert request.expired(created, created + timedelta(seconds=60)) is True


def test_result_serialization_has_only_safe_structured_fields():
    result = LSFAResult("accepted", "connect_email", risk=RiskLevel.MEDIUM, stored_refs={"account": "present"})
    assert result.to_dict() == {
        "status": "accepted",
        "operation": "connect_email",
        "risk": "medium",
        "stored_refs": {"account": "present"},
    }
    assert "password" not in result.to_dict()
