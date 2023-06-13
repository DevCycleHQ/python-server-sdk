# DevCycle Python Server SDK

The DevCycle Python SDK used for feature management.

This SDK allows your application to interface with the [DevCycle Bucketing API](https://docs.devcycle.com/bucketing-api/#tag/devcycle).

## Requirements.

* Python 3.7+

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
from devcycle_python_sdk import DevCycleCloudClient, DevCycleCloudOptions
from devcycle_python_sdk.models.user import User

options = DevCycleCloudOptions()

# create an instance of the client class
dvc = DevCycleCloudClient('YOUR_DVC_SERVER_SDK_KEY', options)

user = User(
    user_id='test',
    email='example@example.ca',
    country='CA'
)

value = dvc.variable_value(user, 'feature-key', 'default-value')
```

## Usage

To find usage documentation, visit our [docs](https://docs.devcycle.com/docs/sdk/server-side-sdks/python#usage).

## Development

When developing the SDK it is recommended that you have both a 3.7 and 3.11 python interpreter installed in order to verify changes across different versions of python.

### Dependencies

To set up dependencies for local development, run:
```
pip install -r requirements.test.txt
```

To run the example app against the local version of the API for testing and development, run:
```sh
pip install --editable .
```
from the top level of the repo (same level as setup.py). Then run the example app as normal.


### Linting

Linting checks on PRs are run using [ruff](https://github.com/charliermarsh/ruff), and are configured using `.ruff.toml`. To run the linter locally, run this command from the top level of the repo:
```
ruff check .
```

Ruff can automatically fix simple linting errors (the ones marked with `[*]`). To do so, run:
```
ruff check . --fix
```

### Unit Tests

To run the unit tests, run:
```bash
python -m unittest -v
```