[![banner](https://raw.githubusercontent.com/oceanprotocol/art/master/github/repo-banner%402x.png)](https://oceanprotocol.com)

# squid-py

> 💧 Python wrapper, allowing to integrate the basic Ocean/web3.py capabilities
> [oceanprotocol.com](https://oceanprotocol.com)

[![PyPI](https://img.shields.io/pypi/v/squid-py.svg)](https://pypi.org/project/squid-py/)
[![Travis (.com)](https://img.shields.io/travis/com/oceanprotocol/squid-py.svg)](https://travis-ci.com/oceanprotocol/squid-py)
[![GitHub contributors](https://img.shields.io/github/contributors/oceanprotocol/squid-py.svg)](https://github.com/oceanprotocol/squid-py/graphs/contributors)
[![Codacy Badge](https://img.shields.io/codacy/grade/7084fbf528934327904a49d458bc46d1.svg)](https://app.codacy.com/project/ocean-protocol/squid-py/dashboard)
[![Codacy coverage](https://img.shields.io/codacy/coverage/7084fbf528934327904a49d458bc46d1.svg)](https://app.codacy.com/project/ocean-protocol/squid-py/dashboard)

---

## Table of Contents

  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Quick-start](#quick-start)
     - [Usage:](#usage)
  - [Configuration](#configuration)
  - [Development](#development)
        - [Code style](#code-style)
        - [Testing](#testing)
        - [New Version / New Release](#new-version-new-release)
  - [License](#license)

---

## Features

Squid-py include the methods to make easy the connection with contracts deployed in different networks.
This repository include also the methods to encrypt and decrypt information using the Parity Secret Store.

## Prerequisites

Python 3.6

## Quick-start

Install Squid:

```
pip install squid-py
```

### Usage:

```python
import os
import time

from squid_py import (
    Ocean,
    ServiceDescriptor,
    ACCESS_SERVICE_TEMPLATE_ID,
    get_service_endpoint,
    get_purchase_endpoint,
)
from squid_py.ddo.metadata import Metadata

# Make a new instance of Ocean
ocean = Ocean('config.ini')  # or Ocean(config_dict)
# You can set a specific ethereum account to use by using `ocean.set_main_account(address, password)`
# Ocean picks up address and password by default from the parity.address and parity.password in the config

# PUBLISHER
# Let's start by registering an asset in the Ocean network
metadata = Metadata.get_example()

# purchase and service endpoints require `brizo.url` is set in the config file
# or passed to Ocean instance in the config_dict.
purchase_endpoint = get_purchase_endpoint(ocean.config)
service_endpoint = get_service_endpoint(ocean.config)
# define the services to include in the new asset DDO
service_descriptor = ServiceDescriptor.access_service_descriptor(2, purchase_endpoint, service_endpoint, 900, ACCESS_SERVICE_TEMPLATE_ID)

ddo = ocean.register_asset(metadata, ocean.main_account.address, service_descriptor)

# Now we have an asset registered, we can verify it exists by resolving the did
_ddo = ocean.resolve_did(ddo.did)
# ddo and _ddo should be identical

# CONSUMER
# search for assets
asset = ocean.search_assets_by_text('Ocean protocol')[0]
# Need some ocean tokens to be able to purchase assets
ocean.main_account.unlock()
ocean.keeper.market.request_tokens(10, ocean.main_account.address)
# Start the purchase/consume request. This will automatically make a payment from the specified account.
service_agreement_id = ocean.sign_service_agreement(asset.did, 0, ocean.main_account.address)
# after a short wait (seconds to minutes) the asset data files should be available in the `downloads.path` defined in config
# wait a bit to let things happen
time.sleep(30)
# Asset files are saved in a folder named after the asset DID
if os.path.exists(ocean.get_asset_folder_path(asset.did, 0)):
    print('asset files downloaded: {}'.format(os.listdir(ocean.get_asset_folder_path(asset.did, 0))))

```

## Configuration

```python
config_dict = {
    'keeper-contracts': {
        # Point to an Ethereum RPC client. Note that Squid learns the name of the network to work with from this client.
        'keeper.url': 'http://localhost:8545',
        # Specify the keeper contracts artifacts folder (has the smart contracts definitions json files). When you
        # install the package, the artifacts are automatically picked up from the `keeper-contracts` Python
        # dependency unless you are using a local ethereum network.
        'keeper.path': 'artifacts',
        'secret_store.url': 'http://localhost:12001',
        'parity.url': 'http://localhost:8545',
        'parity.address': '',
        'parity.password': '',

    },
    'resources': {
        # aquarius is the metadata store. It stores the assets DDO/DID-document
        'aquarius.url': 'http://localhost:5000',
        # Brizo is the publisher's agent. It serves purchase and requests for both data access and compute services
        'brizo.url': 'http://localhost:8030',
        # points to the local database file used for storing temporary information (for instance, pending service agreements).
        'storage.path': 'squid_py.db',
        # Where to store downloaded asset files
        'downloads.path': 'consume-downloads'
    }
}

```

In addition to the configuration file, you may use the following environment variables (override the corresponding configuration file values):

- KEEPER_PATH
- KEEPER_URL
- GAS_LIMIT
- AQUARIUS_URL

## Development

1. Set up a virtual environment

    ```bash
    virtualenv venv -p python3.6
    source venv/bin/activate 
    ```

1. Install requirements

    ```
    pip install -r requirements_dev.txt
    ```

1. Create the local testing environment using [barge](https://github.com/oceanprotocol/barge). Once cloned that repository, you can start the cluster running:

    ```
    ./start_ocean.sh --latest --no-brizo --no-pleuston --local-spree-node
    ```

    It runs an Aquarius node and an Ethereum RPC client. For details, read `docker-compose.yml`.

1. Create local configuration file

    ```
    cp config.ini config_local.ini
    ```

   `config_local.ini` is used by unit tests.

1. Copy keeper artifacts

    A bash script is available to copy keeper artifacts into this file directly from a running docker image. This script needs to run in the root of the project.
    The script waits until the keeper contracts are deployed, and then copies the artifacts.

    ```
    ./scripts/wait_for_migration_and_extract_keeper_artifacts.sh
    ```

    The artifacts contain the addresses of all the deployed contracts and their ABI definitions required to interact with them.

1. Run the unit tests

    ```
    python3 setup.py test
    or
    TEST_TIER=unit python3 setup.py test # where TEST_TIER is unit, integration or e2e to decide which parts of the tests you want to run
    ```

#### Code style

The information about code style in python is documented in this two links [python-developer-guide](https://github.com/oceanprotocol/dev-ocean/blob/master/doc/development/python-developer-guide.md)
and [python-style-guide](https://github.com/oceanprotocol/dev-ocean/blob/master/doc/development/python-style-guide.md).

#### Testing

Automatic tests are setup via Travis, executing `tox`.
Our test use pytest framework.

#### New Version / New Release

See [RELEASE_PROCESS.md](RELEASE_PROCESS.md)

## License

```
Copyright 2018 Ocean Protocol Foundation Ltd.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
