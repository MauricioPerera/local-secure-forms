"""Bounded structural validation before any integrator preflight or effect.

Email/hostname checks are syntax checks only; paths and resource references
require a client-owned preflight to check authority, containment and existence.
"""
import re


def validate_values(fields, values):
    """Return an owned flat copy; never include input in diagnostic messages."""
    if type(values) is not dict or not set(values) <= {f.name for f in fields}:
        raise ValueError('invalid_input')
    validated = {}
    for field in fields:
        if field.name not in values:
            if field.required:
                raise ValueError('missing_field')
            continue
        value = values[field.name]
        if field.type == 'integer':
            valid = type(value) is int and -(2**53 - 1) <= value <= 2**53 - 1
        elif field.type == 'boolean':
            valid = type(value) is bool
        elif field.type == 'email_list':
            valid = (type(value) is list and 1 <= len(value) <= 100 and
                     all(_email(item) for item in value))
        else:
            valid = type(value) is str and 1 <= len(value) <= 65536 and bool(value.strip())
            if valid and field.type == 'email':
                valid = _email(value)
            elif valid and field.type == 'hostname':
                valid = (len(value) <= 253 and all(re.fullmatch(
                    r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?', part)
                    for part in value.split('.')))
            elif valid and field.type == 'opaque_reference':
                valid = bool(re.fullmatch(r'[A-Za-z0-9._:/-]{1,256}', value))
            elif valid and field.type == 'safe_local_path':
                valid = len(value) <= 4096 and not any(ord(c) < 32 for c in value)
        if not valid:
            raise ValueError('invalid_input')
        validated[field.name] = list(value) if type(value) is list else value
    return validated


def _email(value):
    return (type(value) is str and len(value) <= 254 and
            bool(re.fullmatch(r'[^\s@<>\x00-\x1f]+@[^\s@<>\x00-\x1f]+\.[^\s@<>\x00-\x1f]+', value)))
