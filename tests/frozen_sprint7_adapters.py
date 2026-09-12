"""Sprint 7 behavioral contract; migrated to Sprint 13 client issuance API."""
from src.lsfa import GuiAdapter, ManualAdapter, TerminalAdapter


def test_all_modes_share_execution_and_do_not_return_captured_values(harness):
    for mode in (GuiAdapter, TerminalAdapter, ManualAdapter):
        _, ticket, adapter, seen, _ = harness(mode=mode)
        outcome = adapter.run(ticket)
        assert outcome.result.status == 'accepted'
        assert outcome.values_consumed is True
        assert 'password' not in outcome.result.to_dict()
        assert seen == [{'password': 'SYNTHETIC_SENTINEL'}]


def test_cancel_and_decline_never_execute(harness):
    for kwargs, expected in [({'collect': lambda r: None}, 'cancelled'),
                             ({'confirm': lambda c, m: False}, 'declined')]:
        _, ticket, adapter, executed, _ = harness(**kwargs)
        assert adapter.run(ticket).result.status == expected
        assert executed == []


def test_high_risk_uses_pin_without_ui_specific_logic(harness):
    _, ticket, adapter, _, _ = harness(risk='high')
    original = adapter.confirm
    methods = []
    def confirm(context, method):
        methods.append(method)
        return original(context, method)
    adapter.confirm = confirm
    assert adapter.run(ticket).result.status == 'accepted'
    assert methods == ['pin']
