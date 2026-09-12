"""Synthetic structural rejections with stable, value-free diagnostics."""
import pytest
from src.lsfa import FieldSpec, LSFARequest
from src.lsfa.validation import validate_values


@pytest.mark.parametrize('kind,value', [
    ('secret', None), ('secret', ''), ('secret', '  '), ('secret', {'x': 'secret'}),
    ('integer', True), ('integer', 1.5), ('integer', 2**53),
    ('boolean', 1), ('email', 'bad'), ('email', 'a\n@b.test'),
    ('email_list', []), ('email_list', ['a@b.test', None]),
    ('hostname', '-bad.test'), ('hostname', 'bad..test'),
    ('text', 'x' * 65537), ('safe_local_path', 'bad\x00path'),
], ids=[f'invalid-{i}' for i in range(16)])
def test_invalid_values(kind, value):
    field = FieldSpec('value', kind, 'secret' if kind == 'secret' else 'private', True)
    with pytest.raises(ValueError, match='^invalid_input$'):
        validate_values((field,), {'value': value})


@pytest.mark.parametrize('kind,value', [
    ('secret', 'synthetic'), ('integer', 993), ('boolean', False),
    ('email', 'user@example.test'), ('email_list', ['user@example.test']),
    ('hostname', 'imap.example.test'), ('safe_local_path', 'C:/synthetic/file'),
    ('opaque_reference', 'ref:synthetic'), ('text', 'Synthetic'), ('multiline', 'a\nb'),
])
def test_valid_values(kind, value):
    field = FieldSpec('value', kind, 'secret' if kind == 'secret' else 'private', True)
    original = {'value': value}
    result = validate_values((field,), original)
    assert result == original and result is not original
    if type(value) is list:
        assert result['value'] is not value


def test_missing_and_extra():
    field = FieldSpec('password', 'secret', 'secret', True)
    with pytest.raises(ValueError, match='missing_field'):
        validate_values((field,), {})
    with pytest.raises(ValueError, match='invalid_input'):
        validate_values((field,), {'password': 'synthetic', 'extra': True})


def test_request_rejects_duplicate_and_boolean_ttl():
    field = FieldSpec('password', 'secret', 'secret', True)
    for fields, ttl in [((field, field), 60), ((field,), True)]:
        with pytest.raises(ValueError):
            LSFARequest('connect_email', 'Synthetic', fields, {'preflight': 'auth'}, ttl)
