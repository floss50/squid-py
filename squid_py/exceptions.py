"""Exceptions for squid-py."""


class OceanInvalidContractAddress(Exception):
    """Raised when an invalid address is passed to the contract loader."""


class OceanKeeperContractsNotFound(Exception):
    """Raised when is not possible to find the keeper contracts abi."""


class OceanDIDNotFound(Exception):
    """Raised when a requested DID or a DID in the chain cannot be found."""


class OceanDIDUnknownValueType(Exception):
    """Raised when a requested DID or a DID in the chain cannot be found."""


class OceanDIDAlreadyExist(Exception):
    """Raised when a requested DID is already published in OceanDB."""


class OceanInvalidMetadata(Exception):
    """Raised when some value in the metadata is invalid."""


class OceanInvalidServiceAgreementSignature(Exception):
    """Raised when the SLA signature is not valid."""


class OceanServiceAgreementExists(Exception):
    """Raised when the SLA already exists."""


class OceanInvalidTransaction(Exception):
    """Raised when an on-chain transaction fail."""


class OceanInitializeServiceAgreementError(Exception):
    """Error on invoking purchase endpoint"""


class OceanServiceConsumeError(Exception):
    """ Error invoking a consume endpoint"""
