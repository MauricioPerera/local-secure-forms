"""Offline Draft 2020-12 validation; diagnostics never contain input values."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from rfc3339_validator import validate_rfc3339

ROOT = Path(__file__).resolve().parents[1]


def validators():
    formats = FormatChecker()
    formats.checks('date-time')(lambda value: not isinstance(value, str) or validate_rfc3339(value.upper()))
    schemas = {}
    registry = Registry()
    for path in sorted((ROOT / 'schemas').glob('*.json')):
        schema = json.loads(path.read_text(encoding='utf-8'))
        Draft202012Validator.check_schema(schema)
        schemas[path.name] = schema
        registry = registry.with_resource(schema['$id'], Resource.from_contents(schema))
    return {name: Draft202012Validator(schema, registry=registry, format_checker=formats)
            for name, schema in schemas.items()}


def validate(data, schema_name='request.schema.json'):
    try:
        validator = validators()[schema_name]
        if next(validator.iter_errors(data), None) is not None:
            raise ValueError('schema_validation_failed')
        if schema_name == 'request.schema.json':
            names = [field['name'] for field in data['fields']]
            if len(set(names)) != len(names):
                raise ValueError('duplicate_fields')
            presentation = data.get('presentation')
            if isinstance(presentation, dict):
                sections = presentation.get('layout', {}).get('sections')
                if sections is not None:
                    displayed = [name for section in sections for name in section['fields']]
                    if len(displayed) != len(set(displayed)) or set(displayed) != set(names):
                        raise ValueError('presentation_fields_mismatch')
            confirmation = data.get('confirmation', {})
            if ('request_id' in confirmation and
                    confirmation['request_id'] != data.get('request_id')):
                raise ValueError('confirmation_identity_mismatch')
    except Exception:
        # jsonschema errors include rejected input: do not expose them.
        raise ValueError('protocol_validation_failed') from None
    return data
