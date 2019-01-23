"""Test DIDRegistry contract."""
import secrets

from squid_py.keeper.didregistry import DIDRegistry
from tests.resources.tiers import e2e_test, should_run_test

if should_run_test('e2e'):
    did_registry = DIDRegistry('DIDRegistry')


@e2e_test
def test_did_registry_contract():
    assert did_registry
    assert isinstance(did_registry, DIDRegistry)


@e2e_test
def test_did_registry_get_update_at():
    test_id = secrets.token_hex(32)
    assert did_registry.get_update_at(test_id) == 0
