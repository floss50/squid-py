"""
    Test did_lib
"""
import json

from squid_py.ddo import (
    DDO,
    PUBLIC_KEY_STORE_TYPE_PEM,
    PUBLIC_KEY_STORE_TYPE_HEX,
    PUBLIC_KEY_STORE_TYPE_BASE64,
    PUBLIC_KEY_STORE_TYPE_BASE85,
)
from squid_py.did import DID
from squid_py.test_resources.helper_functions import get_resource_path
from ...test_resources.tiers import e2e_test

public_key_store_types = [
    PUBLIC_KEY_STORE_TYPE_PEM,
    PUBLIC_KEY_STORE_TYPE_HEX,
    PUBLIC_KEY_STORE_TYPE_BASE64,
    PUBLIC_KEY_STORE_TYPE_BASE85,
]

TEST_SERVICE_TYPE = 'ocean-meta-storage'
TEST_SERVICE_URL = 'http://localhost:8005'

TEST_METADATA = """
{
   "base": {
     "name": "UK Weather information 2011",
     "type": "dataset",
     "description": "Weather information of UK including temperature and humidity",
     "size": "3.1gb",
     "dateCreated": "2012-10-10T17:00:000Z",
     "author": "Met Office",
     "license": "CC-BY",
     "copyrightHolder": "Met Office",
     "encoding": "UTF-8",
     "compression": "zip",
     "contentType": "text/csv",
     "workExample": "423432fsd,51.509865,-0.118092,2011-01-01T10:55:11+00:00,7.2,68",
     "contentUrls": [
       "https://testocnfiles.blob.core.windows.net/testfiles/testzkp.zip"
     ],
     "links": [
       { "name": "Sample of Asset Data", "type": "sample", "url": "https://foo.com/sample.csv" },
       { "name": "Data Format Definition", "type": "format", "AssetID": "4d517500da0acb0d65a716f61330969334630363ce4a6a9d39691026ac7908ea" }
     ],
     "inLanguage": "en",
     "tags": "weather, uk, 2011, temperature, humidity",
     "price": 10
   },
   "curation": {
     "rating": 0.93,
     "numVotes": 123,
     "schema": "Binary Voting"
   },
   "additionalInformation": {
     "updateFrequency": "yearly",
     "structuredMarkup": [
       {
         "uri": "http://skos.um.es/unescothes/C01194/jsonld",
         "mediaType": "application/ld+json"
       },
       {
         "uri": "http://skos.um.es/unescothes/C01194/turtle",
         "mediaType": "text/turtle"
       }
     ]
   }
}
"""

TEST_SERVICES = [
    {"type": "OpenIdConnectVersion1.0Service",
     "serviceEndpoint": "https://openid.example.com/"
     },
    {
        "type": "CredentialRepositoryService",
        "serviceEndpoint": "https://repository.example.com/service/8377464"
    },
    {
        "type": "XdiService",
        "serviceEndpoint": "https://xdi.example.com/8377464"
    },
    {
        "type": "HubService",
        "serviceEndpoint": "https://hub.example.com/.identity/did:op:0123456789abcdef/"
    },
    {
        "type": "MessagingService",
        "serviceEndpoint": "https://example.com/messages/8377464"
    },
    {
        "type": "SocialWebInboxService",
        "serviceEndpoint": "https://social.example.com/83hfh37dj",
        "values": {
            "description": "My public social inbox",
            "spamCost": {
                "amount": "0.50",
                "currency": "USD"
            }
        }
    },
    {
        "type": "BopsService",
        "serviceEndpoint": "https://bops.example.com/enterprise/"
    },
    {
        "type": "Consume",
        "serviceEndpoint": "http://mybrizo.org/api/v1/brizo/services/consume?pubKey=${pubKey}&serviceId={serviceId}&url={url}"
    },
    {
        "type": "Compute",
        "serviceEndpoint": "http://mybrizo.org/api/v1/brizo/services/compute?pubKey=${pubKey}&serviceId={serviceId}&algo={algo}&container={container}"
    },
]


def generate_sample_ddo():
    did = DID().did
    assert did
    ddo = DDO(did)
    assert ddo
    private_key = ddo.add_signature()

    # add a proof signed with the private key
    ddo.add_proof(0, private_key)

    metadata = json.loads(TEST_METADATA)
    ddo.add_service("Metadata", "http://myaquarius.org/api/v1/provider/assets/metadata/{did}",
                    values={'metadata': metadata})
    for test_service in TEST_SERVICES:
        values = None
        if 'values' in test_service:
            values = test_service['values']

        ddo.add_service(test_service['type'], test_service['serviceEndpoint'], values=values)

    return ddo, private_key


@e2e_test
def test_creating_ddo():
    did = DID().did
    assert did
    ddo = DDO(did)
    assert ddo
    private_keys = []
    for public_key_store_type in public_key_store_types:
        private_keys.append(ddo.add_signature(public_key_store_type))

    assert len(private_keys) == len(public_key_store_types)
    ddo.add_service(TEST_SERVICE_TYPE, TEST_SERVICE_URL)

    assert len(ddo.public_keys) == len(public_key_store_types)
    assert len(ddo.authentications) == len(public_key_store_types)
    assert len(ddo.services) == 1

    ddo_text_no_proof = ddo.as_text()
    assert ddo_text_no_proof
    ddo_text_no_proof_hash = ddo.calculate_hash()

    # test getting public keys in the DDO record
    for index, private_key in enumerate(private_keys):
        assert ddo.get_public_key(index)
        signature_key_id = '{0}#keys={1}'.format(did, index + 1)
        assert ddo.get_public_key(signature_key_id)

    # test validating static proofs
    for index, private_key in enumerate(private_keys):
        ddo.add_proof(index, private_key)
        ddo_text_proof = ddo.as_text()
        assert ddo.validate_proof()
        ddo_text_proof_hash = ddo.calculate_hash()

    ddo = DDO(json_text=ddo_text_proof)
    assert ddo.validate()
    assert ddo.is_proof_defined()
    assert ddo.validate_proof()
    assert ddo.calculate_hash() == ddo_text_proof_hash

    ddo = DDO(json_text=ddo_text_no_proof)
    assert ddo.validate()
    # valid proof should be false since no static proof provided
    assert not ddo.is_proof_defined()
    assert not ddo.validate_proof()
    assert ddo.calculate_hash() == ddo_text_no_proof_hash


@e2e_test
def test_creating_ddo_embedded_public_key():
    did = DID().did
    assert did
    ddo = DDO(did)
    assert ddo
    private_keys = []
    for public_key_store_type in public_key_store_types:
        private_keys.append(ddo.add_signature(public_key_store_type, is_embedded=True))

    assert len(private_keys) == len(public_key_store_types)
    ddo.add_service(TEST_SERVICE_TYPE, TEST_SERVICE_URL)
    # test validating static proofs
    for index, private_key in enumerate(private_keys):
        ddo.add_proof(index, private_key)
        ddo_text_proof = ddo.as_text()
        assert ddo_text_proof
        assert ddo.validate_proof()
        ddo_text_proof_hash = ddo.calculate_hash()
        assert ddo_text_proof_hash


@e2e_test
def test_creating_did_using_ddo():
    # create an empty ddo
    ddo = DDO()
    assert ddo
    private_keys = []
    for public_key_store_type in public_key_store_types:
        private_keys.append(ddo.add_signature(public_key_store_type, is_embedded=True))
    assert len(private_keys) == len(public_key_store_types)
    ddo.add_service(TEST_SERVICE_TYPE, TEST_SERVICE_URL)
    # add a proof to the first public_key/authentication
    ddo.add_proof(0, private_keys[0])
    ddo_text_proof = ddo.as_text()
    assert ddo_text_proof
    assert ddo.validate_proof()


@e2e_test
def test_load_ddo_json():
    # TODO: Fix
    sample_ddo_path = get_resource_path('ddo', 'ddo_sample1.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)
    with open(sample_ddo_path) as f:
        sample_ddo_json_dict = json.load(f)

    sample_ddo_json_string = json.dumps(sample_ddo_json_dict)

    this_ddo = DDO(json_text=sample_ddo_json_string)
    service = this_ddo.get_service('Metadata')
    assert service
    assert service.get_type() == 'Metadata'
    values = service.get_values()
    assert values['metadata']


@e2e_test
def test_ddo_dict():
    sample_ddo_path = get_resource_path('ddo', 'ddo_sample1.json')
    assert sample_ddo_path.exists(), "{} does not exist!".format(sample_ddo_path)

    ddo1 = DDO(json_filename=sample_ddo_path)
    assert ddo1.is_valid
    assert len(ddo1.public_keys) == 3
    assert ddo1.did == 'did:op:3597a39818d598e5d60b83eabe29e337d37d9ed5af218b4af5e94df9f7d9783a'


@e2e_test
def test_generate_test_ddo_files():
    for index in range(1, 3):
        ddo, private_key = generate_sample_ddo()

        json_output_filename = get_resource_path('ddo', 'ddo_sample_generated_{}.json'.format(index))
        with open(json_output_filename, 'w') as fp:
            fp.write(ddo.as_text(is_pretty=True))

        private_output_filename = get_resource_path('ddo', 'ddo_sample_generated_{}_private_key.pem'.format(index))
        with open(private_output_filename, 'w') as fp:
            fp.write(private_key.decode('utf-8'))
