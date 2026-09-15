"""Contrato congelado para presentación declarativa segura."""

import json
from pathlib import Path

import pytest

from scripts.schema_validation import validate
from src.lsfa import (
    AuthorizationStore, FieldSpec, GuiAdapter, LSFARequest, LocalClient,
    ManualAdapter, OperationPolicy,
    PresentationRegistry, PresentationSection, PresentationSpec,
    TerminalAdapter, VerifiedConfirmation,
)

ROOT = Path(__file__).resolve().parents[1]


def _request(presentation):
    fields = (
        FieldSpec("email", "email", "private", True),
        FieldSpec("password", "secret", "secret", True),
    )
    return LSFARequest("connect_email", "Connect", fields, {"preflight": "auth"},
                       60, risk="medium", presentation=presentation)


def test_wire_layout_covers_every_authorized_field_exactly_once():
    sample = json.loads((ROOT / "examples" / "dynamic-presentation.json").read_text("utf-8"))
    assert validate(sample) is sample
    sample["presentation"]["layout"]["sections"][1]["fields"].append("email")
    with pytest.raises(ValueError, match="protocol_validation_failed"):
        validate(sample)


def test_wire_rejects_executable_or_confirmation_content():
    sample = json.loads((ROOT / "examples" / "dynamic-presentation.json").read_text("utf-8"))
    for name, value in (("html", "<input>"), ("script", "send()"),
                        ("url", "https://example.invalid"),
                        ("confirmation", {"method": "user_accept"})):
        candidate = json.loads(json.dumps(sample))
        candidate["presentation"][name] = value
        with pytest.raises(ValueError, match="protocol_validation_failed"):
            validate(candidate)


def test_sdk_rejects_hidden_added_and_repeated_fields():
    for names in (("email",), ("email", "password", "token"),
                  ("email", "password", "password")):
        spec = PresentationSpec(mode="form", sections=(
            PresentationSection("main", "Account", names),))
        with pytest.raises(ValueError, match="presentation fields mismatch"):
            _request(spec)


def test_profile_and_inline_layout_cannot_be_mixed():
    with pytest.raises(ValueError, match="mutually exclusive"):
        PresentationSpec(mode="form", profile="account_v1", sections=(
            PresentationSection("main", "Account", ("email", "password")),))


def test_only_a_locally_registered_profile_can_be_resolved(tmp_path):
    request = _request(PresentationSpec(mode="form", profile="account_v1"))
    fields = request.fields
    policy = OperationPolicy(fields, "auth", lambda values: True,
                             lambda values: {"verified": True}, "medium", ("verified",))
    proof = object()

    def verifier(receipt, context, method):
        if receipt is proof:
            return VerifiedConfirmation(context.binding, method, context.expires_at)

    untrusted = LocalClient({"connect_email": policy},
        AuthorizationStore(tmp_path / "missing.sqlite"), verifier)
    with pytest.raises(ValueError, match="unknown presentation profile"):
        untrusted.issue(request)

    template = PresentationSpec(mode="form", sections=(
        PresentationSection("main", "Account", ("email", "password")),))
    trusted = LocalClient({"connect_email": policy},
        AuthorizationStore(tmp_path / "trusted.sqlite"), verifier,
        presentations=PresentationRegistry({"account_v1": template}))
    ticket = trusted.issue(request)
    assert trusted.resolve_presentation(ticket) == template


def test_presentation_has_no_confirmation_or_executable_surface():
    allowed = set(PresentationSpec.__dataclass_fields__)
    assert allowed == {"mode", "profile", "locale", "theme", "sections"}
    assert not allowed.intersection({"confirmation", "risk", "validator", "execute",
                                     "html", "script", "url"})


def test_legacy_string_presentation_remains_supported(harness):
    client, ticket, adapter, effects, _clock = harness()
    assert client.resolve_presentation(ticket) == PresentationSpec(mode="auto")
    assert adapter.run(ticket).result.status == "accepted"
    assert len(effects) == 1


@pytest.mark.parametrize("adapter_type", [GuiAdapter, TerminalAdapter, ManualAdapter])
def test_all_adapters_keep_the_same_authorization_path(tmp_path, adapter_type):
    fields = (FieldSpec("password", "secret", "secret", True),)
    layout = PresentationSpec(mode=adapter_type.mode, sections=(
        PresentationSection("main", "Credential", ("password",)),))
    request = LSFARequest("save_secret", "Save", fields, {"preflight": "check"},
                          60, risk="low", presentation=layout)
    effects = []
    policy = OperationPolicy(fields, "check", lambda values: True,
                             lambda values: effects.append(values) or {"saved": True},
                             "low", ("saved",))
    proof = object()

    def verifier(receipt, context, method):
        if receipt is proof:
            return VerifiedConfirmation(context.binding, method, context.expires_at)

    client = LocalClient({"save_secret": policy},
        AuthorizationStore(tmp_path / f"{adapter_type.mode}.sqlite"), verifier)
    ticket = client.issue(request)
    adapter = adapter_type(lambda _request: {"password": "SYNTHETIC_SENTINEL"},
                           lambda _context, _method: proof, client=client)
    result = adapter.run(ticket)
    assert result.result.status == "accepted"
    assert result.result.to_dict()["checks"] == {"saved": True}
    assert len(effects) == 1
