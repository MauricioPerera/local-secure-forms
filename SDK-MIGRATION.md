# SDK security migration — Sprint 13

This is a breaking hardening of the experimental reference SDK, not a new
production certification or a complete graphical application.

## Trusted integration boundary

The agent sends data, not Python callbacks. The local application owns the
operation registry, callbacks, authorization database, clock and confirmation
verifier. It must isolate those components from agent code and OS privileges.
Python objects in one interpreter do not isolate an agent from secrets.

`GuiAdapter`, `TerminalAdapter` and `ManualAdapter` are callback adapters. They
do not implement windows, browser protection, terminal secret input, keyring,
PIN enrollment, TOTP verification or factor rate limiting. The integrator must
implement and test those mechanisms. A callback that reads a secret can leak
it deliberately (including through boolean outputs); output validation cannot
sandbox that callback. SDK exceptions are sanitized, but the SDK cannot undo
a callback's own logging, shell commands, network requests or filesystem writes.

## API migration

Old `Adapter(collect, confirm).run(request, execute)` is no longer supported.
Do not wrap old boolean confirmation functions in a verifier returning success.

1. Install an `OperationPolicy` for each operation in trusted application code:
   exact `FieldSpec` tuple, registered preflight name and function, executor,
   minimum risk and an allowlist of boolean result check names.
2. Construct `AuthorizationStore` at one persistent client-owned database path
   shared by all processes. Never create a new database for each request/run.
3. Construct `LocalClient(policies, store, verify_confirmation)` once per local
   session. Call `client.issue(request)` at trusted receipt time, before opening
   a form; do not let the agent supply a creation timestamp or issued ticket.
4. Construct the adapter with `client=client`, `collect(request)` and
   `confirm(context, method)`. Call `adapter.run(ticket)`.
5. `collect` returns a flat dict, or `None` to cancel. `confirm` returns a local
   authenticated receipt, or `False`/`None` to decline. Its context is private
   UI data, not an agent-visible result. Display the exact operation, purpose,
   destination, scope and content; mask credentials. Never render request text
   as executable markup. `summary` hints may not hide effect-relevant fields.
6. The trusted `verify_confirmation(receipt, context, method)` validates actual
   human approval and required factors, then returns `VerifiedConfirmation`
   with the exact context binding, verified method and a deadline no later than
   the ticket's. It returns no evidence on failure. Merely constructing this
   dataclass or receiving a string such as `pin_and_totp` proves nothing.
7. The executor returns only a dict of registered check names with exact boolean
   values. It must raise on an unsuccessful/uncertain action. It must not return
   input values, opaque credential tokens, arbitrary keys, nested objects or
   exception text. A normal return means the integrator reports execution as
   complete; optional check booleans describe observations, not a retry policy.

See `tests/conftest.py` and `tests/frozen_sprint7_adapters.py` for executable
synthetic integrations. Their identity-based verifier is a **test double**,
not a deployable authenticator. Do not copy it as PIN/TOTP verification.

## Policy, values and wire requests

`purge` cannot be registered below `irreversible`. Other operations require an
explicit trusted minimum; `soft_delete` and `restore` are separate registrations
with separate preflight/executor implementations. Unknown operations, field
definitions or preflight names are rejected. Agent-provided risk can only raise
the effective risk. Direct SDK issuance upgrades a lower requested risk; wire
JSON claiming `purge` with lower risk is structurally invalid.

The wire schemas describe presentation/confirmation hints; the Python models
are the execution core, not an automatic JSON deserializer. Validate wire data
with the composed schemas and semantic checks before translating it. The
registered client policy remains authoritative even after structural validation.
`presentation` defaults to `auto` when omitted. The adapter is selected locally.
Public defaults are UI hints, never automatic executor input. Private/secret
defaults are forbidden. Collected values must independently pass validation.

Supported types: `text`, `multiline`, `email`, `email_list`, `hostname`, `integer`,
`boolean`, `secret`, `opaque_reference`, `safe_local_path`. Names are unique;
requests have 1–64 fields; strings are nonblank and bounded to 65536 characters,
emails to 254, hosts to 253, references to 256, paths to 4096, email lists to
100 entries. Integer values exclude booleans and are bounded to ±(2^53−1).
Omitted optional fields are allowed; provided null/empty values are not.
Additional application limits (ports, attachment sizes, accepted addresses)
belong in trusted preflight, not agent-provided executable validators.

Email/hostname validation is deliberately a conservative syntax subset, not
deliverability or DNS validation. A `safe_local_path` type does **not** prove
containment, ACLs, absence of symlinks or overwrite safety. The preflight and
executor must check those conditions against their actual resource operations.
Preflight runs only after structural validation. It may authenticate a service
or inspect a resource, but must not persist credentials or perform the intended
external effect. It must return literal `True`; failures never reach execute.

## Expiry, binding and durable single use

Issuance assigns/preserves a validated non-secret correlation ID and fixes a
deadline of at most 86400 seconds. A keyed HMAC seals the request, identity,
effective risk and deadline. A second keyed binding covers the issued request
and all collected values, including recipients, scope, paths and content.
Callbacks receive copies; they cannot mutate the execution snapshot.

Expiry is checked before capture, after capture/preflight/confirmation/verifier
and immediately before durable consumption. Proofs can expire earlier than
requests. The clock must be trusted; invalid issuance times and time before
issuance are rejected. Administratively rolling a clock backwards within a
valid window is outside the clock assumption. No promise of preventing an
effect already started when its deadline passes is made.

An atomic SQLite transaction changes `pending` to `executing` and records the
content binding before invoking execute. Only one process can claim that ID.
No plaintext captured values or plain password hashes enter this database.
States `accepted`, `executing` and `unknown` cannot be claimed or reissued.
Cancellation/decline/invalid input leave a pending request: within its original
deadline it can collect again, but requires a newly verified bound confirmation.
New requests need distinct IDs and fresh approval; changing IDs is not business
idempotency. For operations needing cross-request deduplication, the integrator
must use a service-side idempotency key in addition to LSFA authorization.

SQLite path, parent permissions, local reliable storage, database integrity and
retention are integrator responsibilities. Do not delete/restore/reset rows to
retry an uncertain effect. The SDK deliberately does not expose a reset API.
Do not use an in-memory/per-run/network database as the durable client ledger.

## Crash and error recovery

An executor exception or invalid output returns `failed` with
`execution_outcome_unknown` and `values_consumed=True`. The effect may already
have occurred. A finalization/storage failure leaves the row locked. An abrupt
process exit can leave `executing` even if no effect occurred; investigate the
external system instead of replaying. The ledger is at-most-once authorization,
not an exactly-once distributed transaction or automatic rollback.

On restart, the process-local HMAC key changes: old pending tickets cannot be
resumed. Preserve the ledger and issue a fresh ID only after any ambiguous
external state has been resolved and the human approves again. Used IDs remain
blocked across restart. Backup rollback or database tampering can defeat replay
protection and is outside the trusted-storage boundary.

## Verification

Use an isolated Python 3.11+ virtual environment (unrelated globally installed
packages may shadow this repository's `src` namespace). From repository root:

```text
python -m pip install -r requirements-dev.txt
python scripts/validate_conformance.py
python scripts/validate_examples.py
python -m pytest tests -q
```

The scripts validate Draft 2020-12 schemas, local composition, formats and
cross-field identities/unique names without retrieving remote schemas. They
are structural validation, not a test of an integrator's GUI or authenticator.
The behavioral suite covers the reference SDK with synthetic callbacks; CI
runs it on Linux, Windows and macOS. Neither result certifies another client.
