"""Pruebas congeladas de los adaptadores de presentación LSFA."""

from src.lsfa import GuiAdapter, ManualAdapter, TerminalAdapter, LSFARequest, FieldSpec


def _request(risk="low"):
    return LSFARequest(
        "connect_email", "Configurar correo",
        (FieldSpec("password", "secret", "secret", True),),
        {"preflight": "auth"}, 60, risk=risk,
    )


def test_all_modes_share_execution_and_do_not_return_captured_values():
    for adapter in (
        GuiAdapter(lambda request: {"password": "no-se-serializa"}, lambda request, method: method == "user_accept"),
        TerminalAdapter(lambda request: {"password": "no-se-serializa"}, lambda request, method: method == "user_accept"),
        ManualAdapter(lambda request: {"password": "no-se-serializa"}, lambda request, method: method == "user_accept"),
    ):
        seen = []
        outcome = adapter.run(_request(), lambda values: seen.append(values) or {"verified": True})
        assert outcome.result.status == "accepted"
        assert outcome.values_consumed is True
        assert "password" not in outcome.result.to_dict()
        assert seen == [{"password": "no-se-serializa"}]


def test_cancel_and_decline_never_execute():
    executed = []
    cancelled = ManualAdapter(lambda request: None, lambda request, method: True)
    declined = TerminalAdapter(lambda request: {"password": "x"}, lambda request, method: False)
    assert cancelled.run(_request(), lambda values: executed.append(values)).result.status == "cancelled"
    assert declined.run(_request(), lambda values: executed.append(values)).result.status == "declined"
    assert executed == []


def test_high_risk_uses_pin_without_ui_specific_logic():
    methods = []
    adapter = GuiAdapter(lambda request: {"password": "x"}, lambda request, method: methods.append(method) or True)
    assert adapter.run(_request("high"), lambda values: {}).result.status == "accepted"
    assert methods == ["pin"]
