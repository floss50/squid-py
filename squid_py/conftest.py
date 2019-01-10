import os

import pytest
from web3 import Web3, HTTPProvider

from squid_py.config import Config
from squid_py.config_provider import ConfigProvider
from squid_py.test_resources.helper_functions import get_registered_ddo, get_consumer_ocean_instance, get_publisher_ocean_instance
from squid_py.test_resources.mocks.secret_store_mock import SecretStoreClientMock
from .test_resources import should_run_test

if should_run_test('e2e'):
    ConfigProvider.set_config(Config('config_local.ini'))


@pytest.fixture
def secret_store():
    return SecretStoreClientMock


@pytest.fixture
def publisher_ocean_instance():
    return get_publisher_ocean_instance()


@pytest.fixture
def consumer_ocean_instance():
    return get_consumer_ocean_instance()


@pytest.fixture
def registered_ddo():
    return get_registered_ddo(get_publisher_ocean_instance())


@pytest.fixture
def web3_instance():
    path_config = 'config_local.ini'
    os.environ['CONFIG_FILE'] = path_config
    config = Config(path_config)
    return Web3(HTTPProvider(config.keeper_url))
