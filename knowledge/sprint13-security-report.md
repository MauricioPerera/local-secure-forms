# Sprint 13 — Security remediation evidence

Status: remediation implemented; exact final-commit CI attestation is maintained
in [PR #1](https://github.com/MauricioPerera/local-secure-forms/pull/1).
Audit base: `fed1723a6e8c73074765fabb1e0fa80bea421a8f`.
Scope: this repository only; synthetic credentials, local databases and effects.

## Baseline reproduction

The audit-base checkout was tested again in isolation before publication of the
fix. Its original adapter API produced these five confirmed conditions:

```json
{
  "expired_capture_executed": true,
  "invalid_input_executed": true,
  "purge_low_executed": true,
  "schema_accepts_weak_purge": true,
  "secret_echo_accepted": true
}
```

The cases used a one-second TTL with 1.05-second capture, a `purge` request at
`low` accepted with `user_accept`, required password `None` plus an extra field,
an executor echoing a synthetic input dict, and direct Draft 2020-12 validation
of a weak purge against the old lifecycle schema. No real service was contacted.
The first four regression tests failed before the fixes. Their setup was
migrated to client issuance when the insecure adapter API was removed; their
security expectations were retained. Frozen Sprint 7 positive/cancel/decline
tests were likewise migrated, not skipped.

## Requirement-to-evidence map

| Contract finding | Correction | Behavioral evidence |
| --- | --- | --- |
| Secret output and callback errors | Registered boolean check names, flat typed outputs, stable errors, unknown outcome after unsafe post-effect output | `test_sprint13_regressions.py`, `test_client_security.py` output/exception cases with synthetic sentinels and stdout/stderr/log capture |
| Expiry and single use | Trusted issuance, keyed identity/content binding, deadline checks, SQLite atomic reservation and durable state | `test_authorization_store.py`, `test_execution_binding.py`, `test_client_security.py` expiry/replay/concurrency cases |
| Risk downgrade | Explicit operation policy, irreversible purge floor, bound evidence from trusted verifier | `test_client_security.py` purge risk matrix, method-name rejection, stale/wrong evidence and all adapter modes |
| Input and preflight | Unique typed fields, bounded flat values, exact client policy/preflight matching, literal-success preflight before executor | `test_input_validation.py`, `test_client_security.py`, null/extra audit regression |
| False conformance | Offline composed Draft 2020-12 schemas, explicit date validator, negative tests, both pytest naming patterns | `test_schema_security.py`, `scripts/schema_validation.py`, `pytest.ini`, CI matrix |

Concurrency tests use sixteen competing calls/connections and assert one
successful reservation/effect. An additional race uses eight independent Python
processes and asserts exactly one success and seven rejected claims. Crash
evidence uses a child Python process that
consumes authorization then exits with `os._exit(17)`; a new connection cannot
consume/reissue the ID. Restarted client tests preserve used-ID rejection.
The durable content binding is checked directly in SQLite; no captured
synthetic secret appears in its dump. This demonstrates at-most-once use,
not exactly-once delivery to an external service.

The final-boundary test also expires a proof earlier than its request. An error
after execution never resets authorization. Unsupported/unknown operations and
validators fail before execution. Reversible operations have distinct policies.

## Verification procedure

In a fresh isolated Python environment from the repository root:

```text
python -m pip install -r requirements-dev.txt
python scripts/validate_conformance.py
python scripts/validate_examples.py
python -m pytest tests -q
git diff --check
```

Current local result: 143 passed on Windows, six examples validated against
four schemas. CI is configured for Python 3.11/3.12/3.13 on Windows, Linux and
macOS; configuration alone is not execution evidence.

Initial full matrix: all nine jobs passed on commit
`34502f10f041a38c68e9af85b2da624ecc45bfcf` in
[run 34704624351](https://github.com/MauricioPerera/local-secure-forms/actions/runs/34704624351).
That run precedes the added eight-process race test. The PR body records the
final head SHA, final run URL and job results after the last update, rather
than trying to embed this document's own commit hash within itself. Completion
requires that final attestation to match the PR head; the initial run alone
does not establish final-commit acceptance.

The final review also rejects trailing newlines in schema identifiers, matching
the Python full-match behavior. Four negative regressions cover operation,
request ID, field name and preflight name; without this check a regex `$`
anchor alone can accept a final newline in some JSON Schema engines.

The requirement-by-requirement review aligned SDK issuance with the wire rule:
purge requests declaring low/medium/high are rejected, not silently upgraded.
An explicitly irreversible purge still requires verified PIN/TOTP evidence.

## Boundaries and migration

`SDK-MIGRATION.md` is the integration contract: the old boolean-confirmation
adapter API is removed. The registry, callbacks, actual verifier, clock and
storage are trusted. The SDK cannot isolate arbitrary callbacks already able
to read secrets, enforce OS ACLs or implement actual GUI/PIN/TOTP enrollment.
It does not certify the separate email CLI or any external integrator.

SPEC, SECURITY, THREAT-MODEL, IMPLEMENTATION-GUIDE, CONFORMANCE and the affected
Sprint 2/3/4/6/7/9 contracts describe these limits. The core/SDK uses the standard
library; schema verification has explicit development dependencies. No real
credentials, email or user data were read or changed by this sprint.
