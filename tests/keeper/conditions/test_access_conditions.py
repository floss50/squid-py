"""Test AccessConditions contract."""
from squid_py.config_provider import ConfigProvider
from squid_py.did import DID, did_to_id
from squid_py.keeper.conditions.access_conditions import AccessConditions
from tests.resources.helper_functions import get_consumer_account
from tests.resources.tiers import e2e_test, should_run_test

if should_run_test('e2e'):
    access_conditions = AccessConditions('AccessConditions')


@e2e_test
def test_access_conditions_contract():
    assert access_conditions
    assert isinstance(access_conditions, AccessConditions), \
        f'{access_conditions} is not instance of AccessConditions'


@e2e_test
def test_check_permissions_not_registered_did():
    consumer_account = get_consumer_account(ConfigProvider.get_config())
    assert not access_conditions.check_permissions(consumer_account.address, did_to_id(DID.did()))

# TODO Create test for check permission after access granted.
