"""
"""

import logging

import pytest

from squid_py.keeper.web3_provider import Web3Provider
from squid_py.ddo import DDO
from squid_py.ocean.asset import Asset
from squid_py.test_resources.helper_functions import get_resource_path

from ...test_resources.tiers import e2e_test

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("web3").setLevel(logging.WARNING)

@e2e_test
def test_create_asset_ddo_file():
    # An asset can be created directly from a DDO .json file
    sample_ddo_path = get_resource_path('ddo', 'ddo_sample1.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    asset1 = Asset.from_ddo_json_file(sample_ddo_path)

    assert isinstance(asset1.ddo, DDO)
    assert asset1.ddo.is_valid

    assert asset1.has_metadata
    print(asset1.metadata)


@e2e_test
def test_register_data_asset_market(publisher_ocean_instance, consumer_ocean_instance):
    """
    Setup accounts and asset, register this asset in Keeper node (On-chain only)
    """
    pub_ocn = publisher_ocean_instance
    cons_ocn = consumer_ocean_instance
    logging.debug("".format())
    asset_price = 100
    sample_ddo_path = get_resource_path('ddo', 'ddo_sample1.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    ##########################################################
    # Setup 2 accounts
    ##########################################################
    aquarius_acct = pub_ocn.main_account
    consumer_acct = cons_ocn.main_account

    # ensure Ocean token balance
    if aquarius_acct.ocean_balance == 0:
        rcpt = aquarius_acct.request_tokens(200)
        Web3Provider.get_web3().eth.waitForTransactionReceipt(rcpt)
    if consumer_acct.ocean_balance == 0:
        rcpt = consumer_acct.request_tokens(200)
        Web3Provider.get_web3().eth.waitForTransactionReceipt(rcpt)

    # You will need some token to make this transfer!
    assert aquarius_acct.ocean_balance > 0
    assert consumer_acct.ocean_balance > 0

    ##########################################################
    # Create an Asset with valid metadata
    ##########################################################

    asset = Asset.from_ddo_json_file(sample_ddo_path)

    ##########################################################
    # Register
    ##########################################################
    # Call the Register function
    result = pub_ocn.keeper.market.register_asset(asset, asset_price, aquarius_acct.address)

    # Check exists
    chain_asset_exists = pub_ocn.keeper.market.check_asset(asset.asset_id)
    logging.debug("check_asset = {}".format(chain_asset_exists))
    assert chain_asset_exists

    # Check price
    chain_asset_price = pub_ocn.keeper.market.get_asset_price(asset.asset_id)
    assert asset_price == chain_asset_price
    logging.debug("chain_asset_price = {}".format(chain_asset_price))


@e2e_test
def test_publish_data_asset_aquarius(publisher_ocean_instance, consumer_ocean_instance):
    """
    Setup accounts and asset, register this asset on Aquarius (MetaData store)
    """
    pub_ocn = publisher_ocean_instance
    cons_ocn = consumer_ocean_instance

    logging.debug("".format())
    sample_ddo_path = get_resource_path('ddo', 'ddo_sample1.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    ##########################################################
    # Setup 2 accounts
    ##########################################################
    aquarius_acct = pub_ocn.main_account
    consumer_acct = cons_ocn.main_account

    # ensure Ocean token balance
    if aquarius_acct.ocean_balance == 0:
        rcpt = aquarius_acct.request_tokens(200)
        Web3Provider.get_web3().eth.waitForTransactionReceipt(rcpt)
    if consumer_acct.ocean_balance == 0:
        rcpt = consumer_acct.request_tokens(200)
        Web3Provider.get_web3().eth.waitForTransactionReceipt(rcpt)

    # You will need some token to make this transfer!
    assert aquarius_acct.ocean_balance > 0
    assert consumer_acct.ocean_balance > 0

    ##########################################################
    # Create an Asset with valid metadata
    ##########################################################
    asset = Asset.from_ddo_json_file(sample_ddo_path)

    ##########################################################
    # List currently published assets
    ##########################################################
    meta_data_assets = pub_ocn.metadata_store.list_assets()
    if meta_data_assets:
        print("Currently registered assets:")
        print(meta_data_assets)

    if asset.did in meta_data_assets:
        pub_ocn.metadata_store.get_asset_ddo(asset.did)
        pub_ocn.metadata_store.retire_asset_ddo(asset.did)
    # Publish the metadata
    pub_ocn.metadata_store.publish_asset_ddo(asset.ddo)

    print("Publishing again should raise error")
    with pytest.raises(ValueError):
        pub_ocn.metadata_store.publish_asset_ddo(asset.ddo)

    # TODO: Ensure returned metadata equals sent!
    # get_asset_metadata only returns 'base' key, is this correct?
    published_metadata = cons_ocn.metadata_store.get_asset_ddo(asset.ddo.did)

    assert published_metadata
    # only compare top level keys
    # assert sorted(list(asset.metadata['base'].keys())) == sorted(list(published_metadata['base'].keys()))
    # asset.metadata == published_metadata
