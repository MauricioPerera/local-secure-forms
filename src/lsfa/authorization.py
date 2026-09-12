"""Client-owned durable authorization state; never stores form values."""
import math
import re
import sqlite3
from pathlib import Path


class AuthorizationError(RuntimeError):
    """Stable failure; callers must not retry external effects automatically."""


class AuthorizationStore:
    """One database shared by all client processes; protected by the integrator.

    A pending request is issued once. Executing survives crashes and cannot be
    claimed again. Recovery requires investigation, never resetting this row.
    Bindings must be keyed digests, not plaintext or plain hashes of passwords.
    """

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    'CREATE TABLE IF NOT EXISTS authorizations ('
                    'request_id TEXT PRIMARY KEY, binding TEXT NOT NULL, '
                    'expires REAL NOT NULL, state TEXT NOT NULL)')
                connection.execute(
                    'CREATE TABLE IF NOT EXISTS execution_bindings ('
                    'request_id TEXT PRIMARY KEY, binding TEXT NOT NULL)')
        finally:
            connection.close()

    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        try:
            connection.execute('PRAGMA synchronous=FULL')
        except Exception:
            connection.close()
            raise
        return connection

    @staticmethod
    def _identity(request_id, binding):
        if not isinstance(request_id, str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,128}', request_id):
            raise AuthorizationError('invalid_request_id')
        if not isinstance(binding, str) or not re.fullmatch(r'[a-f0-9]{64}', binding):
            raise AuthorizationError('invalid_binding')

    @staticmethod
    def _time(value):
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
            raise AuthorizationError('invalid_time')

    def issue(self, request_id, binding, expires_at, now):
        self._identity(request_id, binding)
        self._time(expires_at)
        self._time(now)
        if not now < expires_at <= now + 86400:
            raise AuthorizationError('invalid_deadline')
        connection = self._connect()
        try:
            with connection:
                connection.execute('INSERT INTO authorizations VALUES (?, ?, ?, ?)',
                                   (request_id, binding, expires_at, 'pending'))
        except sqlite3.IntegrityError:
            raise AuthorizationError('request_already_issued') from None
        finally:
            connection.close()

    def consume(self, request_id, binding, now, *, execution_binding=None):
        self._identity(request_id, binding)
        execution_binding = binding if execution_binding is None else execution_binding
        self._identity(request_id, execution_binding)
        self._time(now)
        connection = self._connect()
        try:
            with connection:
                updated = connection.execute(
                    'UPDATE authorizations SET state=? WHERE request_id=? '
                    'AND binding=? AND state=? AND expires>?',
                    ('executing', request_id, binding, 'pending', now))
                if updated.rowcount != 1:
                    raise AuthorizationError('authorization_unavailable')
                connection.execute('INSERT INTO execution_bindings VALUES (?, ?)',
                                   (request_id, execution_binding))
        finally:
            connection.close()

    def finish(self, request_id, state):
        if state not in ('accepted', 'unknown'):
            raise AuthorizationError('invalid_terminal_state')
        connection = self._connect()
        try:
            with connection:
                updated = connection.execute(
                    'UPDATE authorizations SET state=? WHERE request_id=? AND state=?',
                    (state, request_id, 'executing'))
                if updated.rowcount != 1:
                    raise AuthorizationError('invalid_transition')
        finally:
            connection.close()

    def status(self, request_id):
        connection = self._connect()
        try:
            row = connection.execute('SELECT state FROM authorizations WHERE request_id=?',
                                     (request_id,)).fetchone()
            if row is None:
                return 'absent'
            if row[0] not in ('pending', 'executing', 'accepted', 'unknown'):
                raise AuthorizationError('invalid_stored_state')
            return row[0]
        finally:
            connection.close()
