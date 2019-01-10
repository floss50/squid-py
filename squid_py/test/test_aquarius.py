import json
import pytest

from squid_py.ddo import DDO
from squid_py.config import Config
from squid_py.ocean.asset import Asset
from squid_py.ocean.ocean import Ocean
from squid_py.test_resources.helper_functions import get_resource_path
from ..test_resources.tiers import e2e_test

@e2e_test
def test_aquarius():
    ocean_provider = Ocean(Config('config_local.ini'))
    sample_ddo_path = get_resource_path('ddo', 'ddo_sample1.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    asset1 = Asset.from_ddo_json_file(sample_ddo_path)

    # #    print(asset1.ddo.as_text())
    # # Ensure the asset it not already in database
    # ocean_provider.metadata_store.retire_asset_ddo(asset1.did)
    #
    # # Ensure there are no matching assets before publishing
    # for match in ocean_provider.metadata_store.text_search(text='Office'):
    #     ocean_provider.metadata_store.retire_asset_ddo(match['id'])

    if asset1.did in ocean_provider.metadata_store.list_assets():
        ocean_provider.metadata_store.retire_asset_ddo(asset1.did)
    num_assets = len(ocean_provider.metadata_store.list_assets())
    num_matches = len(ocean_provider.metadata_store.text_search(text='Office'))
    ddo_published = ocean_provider.metadata_store.publish_asset_ddo(asset1.ddo)

    ddo = ocean_provider.metadata_store.get_asset_ddo(asset1.did)

    assert ddo_published == ddo

    assert len(ocean_provider.metadata_store.text_search(text='Office')) == (num_matches + 1)

    sample_ddo_path2 = get_resource_path('ddo', 'ddo_sample2.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)
    assert len(ocean_provider.metadata_store.list_assets()) == (num_assets + 1)
    asset2 = Asset.from_ddo_json_file(sample_ddo_path2)

    ocean_provider.metadata_store.update_asset_ddo(asset2.did, asset2.ddo)
    ddo = ocean_provider.metadata_store.get_asset_ddo(asset2.did)
    metadata = ocean_provider.metadata_store.get_asset_metadata(asset2.did)

    # basic test to compare authentication records in the DDO
    ddo = DDO(json_text=json.dumps(ddo))
    assert ddo.authentications[0].as_text() == asset2.ddo.authentications[0].as_text()
    assert 'base' in metadata

    ocean_provider.metadata_store.retire_asset_ddo(asset1.did)
    ocean_provider.metadata_store.retire_asset_ddo(asset2.did)

@e2e_test
def test_error_publishing():
    ocn = Ocean(Config('config_local.ini'))
    with pytest.raises(AttributeError):
        ocn.metadata_store.publish_asset_ddo({})
    with pytest.raises(AttributeError):
        ocn.metadata_store.publish_asset_ddo({"did":"did:op:3809174ce71dd460faf4941140323ebafdc062f062d3932fe0195c78719a8716"})

    sample_ddo_path = get_resource_path('ddo', 'ddo_sample1.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    asset1 = Asset.from_ddo_json_file(sample_ddo_path)

    if asset1.did in ocn.metadata_store.list_assets():
        ocn.metadata_store.retire_asset_ddo(asset1.did)

    ocn.metadata_store.publish_asset_ddo(asset1.ddo)
    with pytest.raises(ValueError):
        ocn.metadata_store.publish_asset_ddo(asset1.ddo)
    with pytest.raises(Exception):
        ocn.metadata_store.retire_asset_ddo('did:op:2133')
    ocn.metadata_store.retire_asset_ddo(asset1.did)
