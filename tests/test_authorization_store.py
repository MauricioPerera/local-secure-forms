from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys

import pytest
from src.lsfa.authorization import AuthorizationStore, AuthorizationError

BINDING = 'a' * 64


def test_consume_is_atomic_across_connections(tmp_path):
    path = tmp_path / 'auth.sqlite'
    AuthorizationStore(path).issue('r', BINDING, 200, 100)
    def attempt(_):
        try:
            AuthorizationStore(path).consume('r', BINDING, 110)
            return 1
        except AuthorizationError:
            return 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        assert sum(executor.map(attempt, range(16))) == 1


@pytest.mark.parametrize('binding,now', [('b' * 64, 110), (BINDING, 200), (BINDING, 201)])
def test_stale_or_different_confirmation_does_not_consume(tmp_path, binding, now):
    store = AuthorizationStore(tmp_path / 'auth.sqlite')
    store.issue('r', BINDING, 200, 100)
    with pytest.raises(AuthorizationError):
        store.consume('r', binding, now)
    assert store.status('r') == 'pending'


def test_crashed_process_cannot_be_replayed(tmp_path):
    path = tmp_path / 'auth.sqlite'
    store = AuthorizationStore(path)
    store.issue('r', BINDING, 200, 100)
    process = subprocess.run([sys.executable, '-c',
        'import os,sys; from src.lsfa.authorization import AuthorizationStore; '
        'AuthorizationStore(sys.argv[1]).consume("r", "a"*64, 110); os._exit(17)',
        str(path)], timeout=15)
    assert process.returncode == 17
    reopened = AuthorizationStore(path)
    assert reopened.status('r') == 'executing'
    with pytest.raises(AuthorizationError):
        reopened.consume('r', BINDING, 111)
    with pytest.raises(AuthorizationError):
        reopened.issue('r', BINDING, 300, 111)


@pytest.mark.parametrize('state', ['accepted', 'unknown'])
def test_terminal_states_cannot_be_replayed(tmp_path, state):
    store = AuthorizationStore(tmp_path / 'auth.sqlite')
    store.issue('r', BINDING, 200, 100)
    store.consume('r', BINDING, 110)
    store.finish('r', state)
    assert store.status('r') == state
    with pytest.raises(AuthorizationError):
        store.consume('r', BINDING, 111)


def test_competing_processes_claim_only_once(tmp_path):
    path = tmp_path / 'process-race.sqlite'
    store = AuthorizationStore(path)
    store.issue('r', BINDING, 200, 100)
    code = '''
import sys
from src.lsfa.authorization import AuthorizationStore, AuthorizationError
store = AuthorizationStore(sys.argv[1])
try:
    store.consume('r', 'a'*64, 110)
except AuthorizationError:
    raise SystemExit(2)
store.finish('r', 'accepted')
'''
    processes = []
    try:
        for _ in range(8):
            processes.append(subprocess.Popen([sys.executable, '-c', code, str(path)]))
        codes = [process.wait(timeout=20) for process in processes]
        assert codes.count(0) == 1
        assert codes.count(2) == 7
        assert store.status('r') == 'accepted'
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
