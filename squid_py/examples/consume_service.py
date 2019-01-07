
def test_consume_flow():
    # This test requires all services running including:
    # secret store
    # parity node
    # aquarius
    # brizo
    # mongodb/bigchaindb

    return
    pub_ocn = get_publisher_ocean_instance()

    # restore the proper http requests client and secret store client
    Brizo.set_http_client(requests)
    # pub_ocn._http_client = requests
    SecretStore.set_client(Client)

    # Register ddo
    ddo = get_registered_ddo(pub_ocn)
    # did = 'did:op:0x96a49018357a4a1e9f179a3a746af5a087559b4ca133499198428dc4b0868731'
    # ddo = consumer_ocean_instance.resolve_did(did)

    path = os.path.join(consumer_ocean_instance._downloads_path, 'testfiles')
    consumer_ocean_instance._downloads_path = path

    # pub_ocn here will be used only to publish the asset. Handling the asset by the publisher
    # will be performed by the Brizo server running locally

    consumer = consumer_ocean_instance.main_account.address

    # sign agreement using the registered asset did above
    service = ddo.get_service(service_type=ServiceTypes.ASSET_ACCESS)
    assert ServiceAgreement.SERVICE_DEFINITION_ID_KEY in service.as_dictionary()
    sa = ServiceAgreement.from_service_dict(service.as_dictionary())
    # This will send the purchase request to Brizo which in turn will execute the agreement on-chain
    service_agreement_id = consumer_ocean_instance.sign_service_agreement(ddo.did,
                                                                          sa.sa_definition_id,
                                                                          consumer)
    print('got new service agreement id:', service_agreement_id)
    filter1 = {'serviceAgreementId': Web3.toBytes(hexstr=service_agreement_id)}
    filter_2 = {'serviceId': Web3.toBytes(hexstr=service_agreement_id)}

    executed = wait_for_event(
        consumer_ocean_instance.keeper.service_agreement.events.ExecuteAgreement, filter1)
    assert executed
    granted = wait_for_event(consumer_ocean_instance.keeper.access_conditions.events.AccessGranted,
                             filter_2)
    assert granted
    fulfilled = wait_for_event(
        consumer_ocean_instance.keeper.service_agreement.events.AgreementFulfilled, filter1)
    assert fulfilled

    path = consumer_ocean_instance._downloads_path
    # check consumed data file in the downloads folder
    assert os.path.exists(path), ''
    folder_names = os.listdir(path)
    assert folder_names, ''
    for name in folder_names:
        asset_path = os.path.join(path, name)
        if os.path.isfile(asset_path):
            continue

        filenames = os.listdir(asset_path)
        assert filenames, 'no files created in this dir'
        assert os.path.isfile(os.path.join(asset_path, filenames[0])), ''

    print('agreement was fulfilled.')
    import shutil
    shutil.rmtree(consumer_ocean_instance._downloads_path)
