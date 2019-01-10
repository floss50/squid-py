"""
    Test Keeper Contracts

    This tests basic contract loading and one call to the smart contract to prove
    that the contact can be loaded and used

"""
import os
import secrets

from squid_py.config import Config
from squid_py.ocean.ocean import Ocean

from ...test_resources.tiers import e2e_test

def get_ocean_instance():
    path_config = 'config_local.ini'
    os.environ['CONFIG_FILE'] = path_config
    ocean = Ocean(Config(os.environ['CONFIG_FILE']))
    return ocean


@e2e_test
def test_didregistry_contract():
    ocean = get_ocean_instance()
    assert ocean

    assert ocean.keeper.did_registry
    test_id = secrets.token_hex(32)
    # contract call does not work with docker
    assert ocean.keeper.did_registry.get_update_at(test_id) == 0


@e2e_test
def test_market_contract():
    ocean = get_ocean_instance()
    assert ocean

    assert ocean.keeper.market
    test_id = secrets.token_hex(32)
    assert ocean.keeper.market.verify_order_payment(test_id)


@e2e_test
def test_token_contract():
    ocean = get_ocean_instance()
    assert ocean

    token_account = list(ocean.accounts)[len(list(ocean.accounts)) - 1]
    assert ocean.keeper.token
    assert ocean.keeper.token.get_token_balance(token_account) == 0
