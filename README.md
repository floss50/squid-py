[![banner](docs/img/repo-banner@2x.png)](https://oceanprotocol.com)

<h1 align="center">ocean-web3</h1>

> 💧 Python wrapper, allowing to integrate the basic Ocean/web3.py capabilities
> [oceanprotocol.com](https://oceanprotocol.com)

## Table of Contents

  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Quick-start](#quick-start)
  - [Code style](#code-style)
  - [Testing](#testing)
  - [License](#license)

---

## Features

Ocean-web3 include the methods to make easy the connection with contracts deployed in different networks.
This repository include also the methods to encrypt and decrypt information.

## Prerequisites

You should have running a instance of BigchainDB and ganache-cli. 
You can start running the docker-compose in the docker directory:

## Quick-start

When you want to interact with the contracts you have to instantiate this class:

```python
from ocean_web3.ocean_contracts import OceanContractsWrapper
ocean = OceanContractsWrapper(host='http://localhost', port=8545, config_path='config.ini')    
ocean.init_contracts()
```
If you do not pass the config_path the wrapper will use the default values. 
After that you have to init the contracts. And you can start to use the methods in the different contracts.

You will find as well two methods that allow you to register and consume an asset.
```python
from ocean_web3.consumer import register, consume
register(publisher_account=ocean.web3.eth.accounts[1],
         provider_account=ocean.web3.eth.accounts[0],
         price=10,
         ocean_contracts_wrapper=ocean,
         json_metadata=json_consume
                          )
consume(resource=resouce_id,
        consumer_account=ocean.web3.eth.accounts[1],
        provider_account=ocean.web3.eth.accounts[0],
        ocean_contracts_wrapper=ocean,
        json_metadata=json_request_consume)

```

## Code style

The information about code style in python is documented in this two links [python-developer-guide](https://github.com/oceanprotocol/dev-ocean/blob/master/doc/development/python-developer-guide.md)
and [python-style-guide](https://github.com/oceanprotocol/dev-ocean/blob/master/doc/development/python-style-guide.md).
    
## Testing

Automatic tests are setup via Travis, executing `tox`.
Our test use pytest framework.


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