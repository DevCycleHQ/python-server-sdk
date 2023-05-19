# DevCycle Python Server SDK

Welcome to the the DevCycle Python SDK, initially generated via the [DevCycle Bucketing API](https://docs.devcycle.com/bucketing-api/#tag/devcycle).

## Requirements.

Python 2.7 and 3.4+

## Installation

```sh
pip install devcycle-python-server-sdk
```
(you may need to run `pip` with root permission: `sudo pip install devcycle-python-server-sdk`)

Then import the package:
```python
import devcycle_python_sdk 
```

## Getting Started

```python
    from __future__ import print_function
    from devcycle_python_sdk import Configuration, DVCOptions, DVCClient, UserData, Event
    from devcycle_python_sdk.rest import ApiException
    configuration = Configuration()
    configuration.api_key['Authorization'] = 'your_server_key_here'
    options = DVCOptions(enableEdgeDB=True)

     # create an instance of the API class
     dvc = DVCClient(configuration, options)
    
     user = UserData(
        user_id='test',
        email='example@example.ca',
        country='CA'
    )

    value = dvc.variable_value(user, 'feature-key', 'default-value')
```

## Usage

To find usage documentation, visit our [docs](https://docs.devcycle.com/docs/sdk/server-side-sdks/python#usage).

## Development

To set up dependencies for local development, run:
```
pip install -r requirements.test.txt
```

To run the example app against the local version of the API for testing and development, run:
```sh
pip install --editable .
```
from the top level of the repo (same level as setup.py). Then run the example app as normal.


Linting checks on PRs are run using [ruff](https://github.com/charliermarsh/ruff), and are configured using `.ruff.toml`. To run the linter locally, run this command from the top level of the repo:
```
ruff check .
```

Ruff can automatically fix simple linting errors (the ones marked with `[*]`). To do so, run:
```
ruff check . --fix
```