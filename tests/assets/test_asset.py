"""Test Assets"""

import logging

from squid_py.agreements.service_factory import ServiceDescriptor, ServiceTypes
from squid_py.ddo.ddo import DDO
from squid_py.keeper.web3_provider import Web3Provider
from tests.resources.helper_functions import get_resource_path
from tests.resources.tiers import e2e_test

logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("web3").setLevel(logging.WARNING)


@e2e_test
def test_create_asset_ddo_file():
    # An asset can be created directly from a DDO .json file
    sample_ddo_path = get_resource_path('ddo', 'ddo_sample1.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    asset1 = DDO(json_filename=sample_ddo_path)

    assert isinstance(asset1, DDO)
    assert asset1.is_valid

    assert asset1.metadata


@e2e_test
def test_create_data_asset(publisher_ocean_instance, consumer_ocean_instance):
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
    if pub_ocn.accounts.balance(aquarius_acct).ocn == 0:
        rcpt = pub_ocn.accounts.request_tokens(aquarius_acct, 200)
        Web3Provider.get_web3().eth.waitForTransactionReceipt(rcpt)
    if cons_ocn.accounts.balance(consumer_acct).ocn == 0:
        rcpt = cons_ocn.accounts.request_tokens(consumer_acct, 200)
        Web3Provider.get_web3().eth.waitForTransactionReceipt(rcpt)

    # You will need some token to make this transfer!
    assert pub_ocn.accounts.balance(aquarius_acct).ocn > 0
    assert cons_ocn.accounts.balance(consumer_acct).ocn > 0

    ##########################################################
    # Create an Asset with valid metadata
    ##########################################################
    asset = DDO(json_filename=sample_ddo_path)

    ##########################################################
    # List currently published assets
    ##########################################################
    meta_data_assets = pub_ocn.assets.search('')
    if meta_data_assets:
        print("Currently registered assets:")
        print(meta_data_assets)

    if asset.did in meta_data_assets:
        pub_ocn.assets.resolve(asset.did)
        pub_ocn.assets.retire(asset.did)
    # Publish the metadata
    new_asset = pub_ocn.assets.create(asset.metadata, aquarius_acct)

    # TODO: Ensure returned metadata equals sent!
    # get_asset_metadata only returns 'base' key, is this correct?
    published_metadata = cons_ocn.assets.resolve(new_asset.did)

    assert published_metadata
    # only compare top level keys
    assert sorted(list(asset.metadata['base'].keys())).remove('files') == sorted(
        list(published_metadata.metadata['base'].keys())).remove('encryptedFiles')


def test_create_asset_with_different_secret_store(publisher_ocean_instance):
    ocn = publisher_ocean_instance

    sample_ddo_path = get_resource_path('ddo', 'ddo_sample1.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    acct = ocn.main_account

    asset = DDO(json_filename=sample_ddo_path)
    my_secret_store = 'http://myownsecretstore.com'
    auth_service = ServiceDescriptor.authorization_service_descriptor(my_secret_store)
    new_asset = ocn.assets.create(asset.metadata, acct, [auth_service])
    assert new_asset.get_service(ServiceTypes.AUTHORIZATION).endpoints.consume == my_secret_store
    assert new_asset.get_service(ServiceTypes.ASSET_ACCESS)
    assert new_asset.get_service(ServiceTypes.METADATA)

    new_asset = ocn.assets.create(asset.metadata, acct)
    assert new_asset.get_service(ServiceTypes.AUTHORIZATION)
    assert new_asset.get_service(ServiceTypes.ASSET_ACCESS)
    assert new_asset.get_service(ServiceTypes.METADATA)

    access_service = ServiceDescriptor.access_service_descriptor(
        2, 'purchase', 'consume', 35, ''
    )
    new_asset = ocn.assets.create(asset.metadata, acct, [access_service])
    assert new_asset.get_service(ServiceTypes.AUTHORIZATION)
    assert new_asset.get_service(ServiceTypes.ASSET_ACCESS)
    assert new_asset.get_service(ServiceTypes.METADATA)
