"""Validate examples against the composed LSFA schemas, fully offline."""
import json
from pathlib import Path
import sys
if __package__:
    from .schema_validation import validate
else:
    from schema_validation import validate


def validate_request(path):
    return validate(json.loads(path.read_text(encoding='utf-8')))


def main():
    root = Path(__file__).resolve().parents[1]
    paths = sorted((root / 'examples').glob('*.json'))
    if not paths:
        raise ValueError('examples_missing')
    for path in paths:
        validate_request(path)
    print(f'OK: {len(paths)} ejemplos LSFA validos (Draft 2020-12)')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('ERROR: example_validation_failed', file=sys.stderr)
        raise SystemExit(1)
