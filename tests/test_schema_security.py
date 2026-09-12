"""Actual Draft 2020-12 validation, not keyword-presence assertions."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.schema_validation import validate

ROOT = Path(__file__).resolve().parents[1]


def example(name='connect-email'):
    return json.loads((ROOT / 'examples' / f'{name}.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('name', ['connect-email', 'send-email', 'purge', 'soft-delete', 'restore', 'extract-attachment'])
def test_positive_examples(name):
    assert validate(example(name))


@pytest.mark.parametrize('fault', ['secret_default', 'private_default', 'duplicate', 'ttl_bool',
    'ttl_large', 'unknown_type', 'unknown_property', 'unknown_validation', 'weak_method',
    'no_single_use', 'not_required', 'wrong_summary', 'wrong_identity', 'bad_date'])
def test_reject_invalid_wire_requests(fault):
    data = example()
    if fault == 'secret_default':
        data['fields'][1]['default'] = 'SYNTHETIC_SENTINEL'
    elif fault == 'private_default':
        data['fields'][0]['default'] = 'SYNTHETIC_SENTINEL'
    elif fault == 'duplicate':
        data['fields'].append(deepcopy(data['fields'][0]))
    elif fault == 'ttl_bool':
        data['expires_in_seconds'] = True
    elif fault == 'ttl_large':
        data['expires_in_seconds'] = 86401
    elif fault == 'unknown_type':
        data['fields'][0]['type'] = 'eval'
    elif fault == 'unknown_property':
        data['extra'] = True
    elif fault == 'unknown_validation':
        data['validation']['code'] = 'SYNTHETIC_SENTINEL'
    elif fault == 'weak_method':
        data['risk'] = 'high'
    elif fault == 'no_single_use':
        del data['confirmation']['single_use']
    elif fault == 'not_required':
        data['confirmation']['required'] = False
    elif fault == 'wrong_summary':
        data['confirmation']['summary'] = 'text'
    elif fault == 'wrong_identity':
        data['request_id'] = 'one'
        data['confirmation']['request_id'] = 'another'
    else:
        data['confirmation']['expires_at'] = 'invalid'
    with pytest.raises(ValueError, match='^protocol_validation_failed$'):
        validate(data)


@pytest.mark.parametrize('risk', ['low', 'medium', 'high'])
def test_purge_downgrade_fails_both_schemas(risk):
    data = example('purge')
    data['risk'] = risk
    with pytest.raises(ValueError):
        validate(data)
    with pytest.raises(ValueError):
        validate({'operation': 'purge', 'resource_ref': 'synthetic',
                  'risk': risk, 'confirmation': 'user_accept'}, 'lifecycle.schema.json')


@pytest.mark.parametrize('checks', [{'verified': 'SYNTHETIC_SENTINEL'},
    {'verified': {'nested': 'SYNTHETIC_SENTINEL'}}, {'verified': 1}])
def test_result_schema_rejects_nonboolean_checks(checks):
    with pytest.raises(ValueError):
        validate({'status': 'accepted', 'operation': 'connect_email', 'checks': checks},
                 'result.schema.json')


def test_confirmation_and_lifecycle_positive():
    validate({'method': 'pin_and_totp', 'required': True, 'single_use': True},
             'confirmation.schema.json')
    validate({'operation': 'purge', 'resource_ref': 'synthetic', 'risk': 'irreversible',
              'confirmation': 'pin_and_totp'}, 'lifecycle.schema.json')
