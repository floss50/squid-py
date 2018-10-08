from squid_py.config_parser import load_config_section
from squid_py.constants import KEEPER_CONTRACTS
from squid_py.ocean import Ocean
from squid_py.utils.web3_helper import convert_to_bytes, convert_to_string, convert_to_text
import logging
import os


def test_ocean_contracts():
    os.environ['CONFIG_FILE'] = 'config_local.ini'
    os.environ['KEEPER_HOST'] = 'http://0.0.0.0'
    os.environ['KEEPER_PORT'] = '8545'
    ocean = Ocean()
    assert ocean.token is not None


def test_ocean_contracts_with_conf(caplog):
    caplog.set_level(logging.DEBUG)
    # Need to ensure config.ini is populated!
    ocean = Ocean(host='http://0.0.0.0', port=8545, config_path='config_local.ini')
    conf = load_config_section('config_local.ini', KEEPER_CONTRACTS)
    assert ocean.market.address == ocean.web3.toChecksumAddress(conf['market.address'])


def test_split_signature():
    ocean = Ocean(host='http://0.0.0.0', port=8545, config_path='config_local.ini')
    signature = b'\x19\x15!\xecwnX1o/\xdeho\x9a9\xdd9^\xbb\x8c2z\x88!\x95\xdc=\xe6\xafc\x0f\xe9\x14\x12\xc6\xde\x0b\n\xa6\x11\xc0\x1cvv\x9f\x99O8\x15\xf6f\xe7\xab\xea\x982Ds\x0bX\xd9\x94\xa42\x01'
    split_signature = ocean.helper.split_signature(signature=signature)
    assert split_signature.v == 28
    assert split_signature.r == b'\x19\x15!\xecwnX1o/\xdeho\x9a9\xdd9^\xbb\x8c2z\x88!\x95\xdc=\xe6\xafc\x0f\xe9'
    assert split_signature.s == b'\x14\x12\xc6\xde\x0b\n\xa6\x11\xc0\x1cvv\x9f\x99O8\x15\xf6f\xe7\xab\xea\x982Ds\x0bX\xd9\x94\xa42'


def test_convert():
    input_text = "my text"
    print("output %s" % convert_to_string(convert_to_bytes(input_text)))
    assert convert_to_text(convert_to_bytes(input_text)) == input_text