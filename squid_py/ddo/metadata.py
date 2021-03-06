"""DID Lib to do DID's and DDO's."""


class AdditionalInfoMeta(object):
    """Attributes that can enhance the discoverability of a resource."""
    KEY = 'additionalInformation'
    VALUES_KEYS = (
        "updateFrequency",
        "structuredMarkup"
    )
    REQUIRED_VALUES_KEYS = tuple()
    EXAMPLE = {
        "updateFrequency": "yearly",
        "structuredMarkup": [
            {
                "uri": "http://skos.um.es/unescothes/C01194/jsonld",
                "mediaType": "application/ld+json",
            },
            {
                "uri": "http://skos.um.es/unescothes/C01194/turtle",
                "mediaType": "text/turtle",
            },
        ],
    }


class CurationMeta(object):
    """To normalize the different possible rating attributes after a curation process."""
    KEY = 'curation'
    VALUES_KEYS = (
        "rating", "numVotes", "schema"
    )
    REQUIRED_VALUES_KEYS = tuple()
    EXAMPLE = {
        "rating": 0.93,
        "numVotes": 123,
        "schema": "Binary Voting",
    }


class MetadataBase(object):
    """The base attributes are recommended to be included in the Asset Metadata."""
    KEY = 'base'
    VALUES_KEYS = {
        'name',
        'type',
        'description',
        'size',
        'dateCreated',
        'author',
        'license',
        'copyrightHolder',
        'encoding',
        'compression',
        'contentType',
        'workExample',
        'links',
        'inLanguage',
        'tags',
        'price',
        'links',
        'files',
        'categories'
    }
    REQUIRED_VALUES_KEYS = {'name', 'dateCreated', 'author', 'license', 'contentType', 'price',
                            'files'}

    EXAMPLE = {
        'name': "Ocean protocol white paper",
        'type': "dataset",
        'description': "Introduce the main concepts and vision behind ocean protocol",
        'size': "1mb",
        'dateCreated': "2012-10-10T17:00:000Z",
        'author': "Ocean Protocol Foundation Ltd.",
        'license': "CC-BY",
        'copyrightHolder': "Ocean Protocol Foundation Ltd.",
        'encoding': "UTF-8",
        'compression': "",
        'contentType': "text/csv",
        'workExample': "Text PDF",
        'inLanguage': "en",
        'categories': ["white-papers"],
        'tags': "data exchange sharing curation bonding curve",
        'price': 23,
        'files': [
            {
                "url": "https://testocnfiles.blob.core.windows.net/testfiles/testzkp.pdf",
                "checksum": "efb2c764274b745f5fc37f97c6b0e761",
                "checksumType": "MD5",
                "contentLength": "4535431",
                "resourceId": "access-log2018-02-13-15-17-29-18386C502CAEA932"
            },
            {
                "url": "s3://ocean-test-osmosis-data-plugin-dataseeding-1537375953/data.txt",
                "checksum": "efb2c764274b745f5fc37f97c6b0e761",
                "contentLength": "4535431",
                "resourceId": "access-log2018-02-13-15-17-29-18386C502CAEA932"
            },
            {
                "url": "http://www3.cs.stonybrook.edu/~algorith/implement/graphbase/distrib/cweb3"
                       ".4e.tar.gz"
            },
        ],
        'links': [
            {
                "sample1": "http://data.ceda.ac.uk/badc/ukcp09/data/gridded-land-obs/gridded-land"
                           "-obs-daily/",
            },
            {
                "sample2": "http://data.ceda.ac.uk/badc/ukcp09/data/gridded-land-obs/gridded-land"
                           "-obs-averages-25km/",
            },
            {
                "fieldsDescription": "http://data.ceda.ac.uk/badc/ukcp09/",
            },

        ],
    }


class Metadata(object):
    """Every Asset (dataset, algorithm, etc.) in the Ocean Network has an associated Decentralized
    Identifier (DID) and DID document / DID Descriptor Object (DDO)."""
    REQUIRED_SECTIONS = {MetadataBase.KEY, }
    MAIN_SECTIONS = {
        MetadataBase.KEY: MetadataBase,
        CurationMeta.KEY: CurationMeta,
        AdditionalInfoMeta.KEY: AdditionalInfoMeta
    }

    @staticmethod
    def validate(metadata):
        """Validator of the metadata composition

        :param metadata: Metadata
        :return: bool
        """
        # validate required sections and their sub items
        for section_key in Metadata.REQUIRED_SECTIONS:
            if section_key not in metadata or not metadata[section_key] or not isinstance(
                    metadata[section_key], dict):
                return False

            section = Metadata.MAIN_SECTIONS[section_key]
            section_metadata = metadata[section_key]
            for subkey in section.REQUIRED_VALUES_KEYS:
                if subkey not in section_metadata or section_metadata[subkey] is None:
                    return False

        return True

    @staticmethod
    def get_example():
        """Retrieve an example of the metadata"""
        example = dict()
        for section_key, section in Metadata.MAIN_SECTIONS.items():
            example[section_key] = section.EXAMPLE.copy()

        return example
