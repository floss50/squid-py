"""Test Token Contract."""
import pytest

from squid_py.config_provider import ConfigProvider
from squid_py.keeper import Keeper
from squid_py.keeper.token import Token
from tests.resources.helper_functions import get_publisher_account, get_consumer_account
from tests.resources.tiers import e2e_test

token = Token('OceanToken')
consumer_account = get_consumer_account(ConfigProvider.get_config())
publisher_account = get_publisher_account(ConfigProvider.get_config())


@e2e_test
def test_token_contract():
    assert token
    assert isinstance(token, Token)


@e2e_test
def test_get_balance():
    assert isinstance(token.get_token_balance(consumer_account.address), int)


@e2e_test
def test_get_balance_invalid_address():
    with pytest.raises(Exception):
        token.get_token_balance('not valid')


@e2e_test
def test_token_approve():
    Keeper.get_instance().unlock_account(publisher_account)
    assert token.token_approve(consumer_account.address, 100, publisher_account)


@e2e_test
def test_token_approve_invalid_address():
    with pytest.raises(Exception):
        Keeper.get_instance().unlock_account(publisher_account)
        token.token_approve('10923019', 100, publisher_account)


@e2e_test
def test_token_approve_invalid_tokens():
    with pytest.raises(Exception):
        Keeper.get_instance().unlock_account(publisher_account)
        token.token_approve(consumer_account.address, -100, publisher_account)
