import json

from squid_py.agreements.service_agreement_condition import Event, ServiceAgreementCondition


class ServiceAgreementTemplate(object):
    """Class representing a Service Agreement Template."""
    DOCUMENT_TYPE = 'Access'
    TEMPLATE_ID_KEY = 'templateId'

    def __init__(self, template_json=None):
        self.template_id = ''
        self.name = ''
        self.creator = ''
        self.template = {}
        if template_json:
            self.parse_template_json(template_json)

    @classmethod
    def from_json_file(cls, path):
        """

        :param path:
        :return:
        """
        with open(path) as jsf:
            template_json = json.load(jsf)
            return cls(template_json=template_json)

    def parse_template_json(self, template_json):
        """

        :param template_json:
        :return:
        """
        assert template_json['type'] == self.DOCUMENT_TYPE, ''
        self.template_id = template_json['templateId']
        self.name = template_json.get('name')
        self.creator = template_json.get('creator')
        self.template = template_json['serviceAgreementTemplate']

    def set_template_id(self, template_id):
        """

        :param template_id:
        :return:
        """
        self.template_id = template_id

    @property
    def fulfillment_order(self):
        """

        :return:
        """
        return self.template['fulfillmentOrder']

    @property
    def condition_dependency(self):
        """

        :return:
        """
        return self.template['conditionDependency']

    @property
    def contract_name(self):
        """

        :return:
        """
        return self.template['contractName']

    @property
    def agreement_events(self):
        """

        :return:
        """
        return [Event(e) for e in self.template['events']]

    @property
    def conditions(self):
        """

        :return:
        """
        return [
            ServiceAgreementCondition(cond_json) for cond_json in self.template['conditions']
        ]

    def set_conditions(self, conditions):
        """

        :param conditions:
        :return:
        """
        self.template['conditions'] = [cond.as_dictionary() for cond in conditions]

    def as_dictionary(self):
        """

        :return:
        """
        template = {
            'contractName': self.contract_name,
            'events': [e.as_dictionary() for e in self.agreement_events],
            'fulfillmentOrder': self.fulfillment_order,
            'conditionDependency': self.condition_dependency,
            'conditions': [cond.as_dictionary() for cond in self.conditions]
        }
        return {
            # 'type': self.DOCUMENT_TYPE,
            'name': self.name,
            'creator': self.creator,
            'serviceAgreementTemplate': template
        }

    @staticmethod
    def example_dict():
        return {
            "type": "Access",
            "templateId": "0x044852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d",
            "name": "dataAssetAccessServiceAgreement",
            "creator": "",
            "serviceAgreementTemplate": {
                "contractName": "EscrowAccessSecretStoreTemplate",
                "events": [
                    {
                        "name": "AgreementCreated",
                        "actorType": "consumer",
                        "handler": {
                            "moduleName": "escrowAccessSecretStoreTemplate",
                            "functionName": "fulfillLockRewardCondition",
                            "version": "0.1"
                        }
                    }
                ],
                "fulfillmentOrder": [
                    "lockReward.fulfill",
                    "accessSecretStore.fulfill",
                    "escrowReward.fulfill"
                ],
                "conditionDependency": {
                    "lockReward": [],
                    "grantSecretStoreAccess": [],
                    "releaseReward": [
                        "lockReward",
                        "accessSecretStore"
                    ]
                },
                "conditions": [
                    {
                        "name": "lockReward",
                        "timelock": 0,
                        "timeout": 0,
                        "contractName": "LockRewardCondition",
                        "functionName": "fulfill",
                        "parameters": [
                            {
                                "name": "_rewardAddress",
                                "type": "address",
                                "value": ""
                            },
                            {
                                "name": "_amount",
                                "type": "uint256",
                                "value": ""
                            }
                        ],
                        "events": [
                            {
                                "name": "Fulfilled",
                                "actorType": "publisher",
                                "handler": {
                                    "moduleName": "lockRewardCondition",
                                    "functionName": "fulfillAccessSecretStoreCondition",
                                    "version": "0.1"
                                }
                            }
                        ]
                    },
                    {
                        "name": "accessSecretStore",
                        "timelock": 0,
                        "timeout": 0,
                        "contractName": "AccessSecretStoreCondition",
                        "functionName": "fulfill",
                        "parameters": [
                            {
                                "name": "_documentId",
                                "type": "bytes32",
                                "value": ""
                            },
                            {
                                "name": "_grantee",
                                "type": "address",
                                "value": ""
                            }
                        ],
                        "events": [
                            {
                                "name": "Fulfilled",
                                "actorType": "publisher",
                                "handler": {
                                    "moduleName": "accessSecretStore",
                                    "functionName": "fulfillEscrowRewardCondition",
                                    "version": "0.1"
                                }
                            },
                            {
                                "name": "TimedOut",
                                "actorType": "consumer",
                                "handler": {
                                    "moduleName": "accessSecretStore",
                                    "functionName": "fulfillEscrowRewardCondition",
                                    "version": "0.1"
                                }
                            }
                        ]
                    },
                    {
                        "name": "escrowReward",
                        "timelock": 0,
                        "timeout": 0,
                        "contractName": "EscrowReward",
                        "functionName": "fulfill",
                        "parameters": [
                            {
                                "name": "_amount",
                                "type": "uint256",
                                "value": ""
                            },
                            {
                                "name": "_receiver",
                                "type": "address",
                                "value": ""
                            },
                            {
                                "name": "_sender",
                                "type": "address",
                                "value": ""
                            },
                            {
                                "name": "_lockCondition",
                                "type": "bytes32",
                                "value": ""
                            },
                            {
                                "name": "_releaseCondition",
                                "type": "bytes32",
                                "value": ""
                            }
                        ],
                        "events": [
                            {
                                "name": "Fulfilled",
                                "actorType": "publisher",
                                "handler": {
                                    "moduleName": "escrowRewardCondition",
                                    "functionName": "verifyRewardTokens",
                                    "version": "0.1"
                                }
                            }
                        ]
                    }
                ]
            }
        }
