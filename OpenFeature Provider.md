# OpenFeature DevCycle Python Provider

This library provides a Python implementation of the [OpenFeature](https://openfeature.dev/) Provider interface for DevCycle.

## Example App

See the [example app](/example/openfeature_example.py) for a working example of the OpenFeature DevCycle Python Provider.

## Usage

See our [documentation](https://docs.devcycle.com/sdk/server-side-sdks/python) for more information.

Create the appropriate DevCycle SDK client first (`DevCycleLocalClient` or `DevCycleCloudClient`), then pass it to the `DevCycleProvider` and set it as the provider for OpenFeature.

```python
from openfeature import api
from openfeature.evaluation_context import EvaluationContext

from devcycle_python_sdk import DevCycleLocalClient, DevCycleLocalOptions
from devcycle_python_sdk.openfeature.provider import DevCycleProvider


# Initialize the DevCycle SDK
devcycle_client = DevCycleLocalClient("DEVCYCLE_SERVER_SDK_KEY", DevCycleLocalOptions())

# Set the initialzed DevCycle client as the provider for OpenFeature
api.set_provider(DevCycleProvider(devcycle_client))

# Get the OpenFeature client
open_feature_client = api.get_client()

# Set the global context for the OpenFeature client, you can use "targetingKey" or "user_id"
# This can also be done on a request basis instead
api.set_evaluation_context(EvaluationContext(targeting_key="test-1234"))

# Retrieve a boolean flag from the OpenFeature client
bool_flag = open_feature_client.get_boolean_value("bool-flag", False)
```

#### Required TargetingKey

For DevCycle SDK to work we require either a `targeting_key` or `user_id` to be set on the OpenFeature context. 
This is used to identify the user as the `user_id` for a `DevCycleUser` in DevCycle.

#### Context properties to DevCycleUser

The provider will automatically translate known `DevCycleUser` properties from the OpenFeature context to the `DevCycleUser` object.
[DevCycleUser Python Interface](https://github.com/DevCycleHQ/python-server-sdk/blob/main/devcycle_python_sdk/models/user.py#L8)

For example all these properties will be set on the `DevCycleUser`:
```python
context = EvaluationContext(targeting_key="test-1234", attributes={
    "email": "email@devcycle.com",
    "name": "name",
    "language": "en",
    "country": "CA",
    "appVersion": "1.0.11",
    "appBuild": 1000,
    "customData": {"custom": "data"},
    "privateCustomData": {"private": "data"}
})
```

Context properties that are not known `DevCycleUser` properties will be automatically 
added to the `customData` property of the `DevCycleUser`.

#### Context Limitations

DevCycle only supports flat JSON Object properties used in the Context. Non-flat properties will be ignored.

For example `obj` will be ignored: 
```python
context = EvaluationContext(targeting_key="test-1234", attributes={
    "obj": { "key": "value" }
})
```

#### JSON Flag Limitations

The OpenFeature spec for JSON flags allows for any type of valid JSON value to be set as the flag value.

For example the following are all valid default value types to use with OpenFeature:
```python
# Invalid JSON values for the DevCycle SDK, will return defaults
open_feature_client.get_object_value("json-flag", ["array"])
open_feature_client.get_object_value("json-flag", 610)
open_feature_client.get_object_value("json-flag", false)
open_feature_client.get_object_value("json-flag", "string")
open_feature_client.get_object_value("json-flag", null)
```

However, these are not valid types for the DevCycle SDK, the DevCycle SDK only supports JSON Objects:
```python
# Valid JSON Object as the default value, will be evaluated by the DevCycle SDK
open_feature_client.get_object_value("json-flag", { "default": "value" })
```