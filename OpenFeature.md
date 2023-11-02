# DevCycle Python SDK OpenFeature Provider

This SDK provides a Python implementation of the [OpenFeature](https://openfeature.dev/) Provider interface. 

## Example App

See the [example app](/example/openfeature_example.py) for a working example using DevCycle Python SDK OpenFeature Provider.

## Usage

See our [documentation](https://docs.devcycle.com/sdk/server-side-sdks/python) for more information.

Instantiate and configure the DevCycle SDK client first, either `DevCycleLocalClient` or `DevCycleCloudClient`. 

Once the DevCycle client is configured, call the `devcycle_client.get_openfeature_provider()` function to obtain the OpenFeature provider. 

```python
from openfeature import api
from openfeature.evaluation_context import EvaluationContext

from devcycle_python_sdk import DevCycleLocalClient, DevCycleLocalOptions

# Initialize the DevCycle SDK
devcycle_client = DevCycleLocalClient("DEVCYCLE_SERVER_SDK_KEY", DevCycleLocalOptions())

# Set the initialzed DevCycle client as the provider for OpenFeature
api.set_provider(devcycle_client.get_openfeature_provider())

# Get the OpenFeature client
open_feature_client = api.get_client()

# Set the global context for the OpenFeature client, you can use "targetingKey" or "user_id"
# This can also be done on a request basis instead
api.set_evaluation_context(EvaluationContext(targeting_key="test-1234"))

# Retrieve a boolean flag from the OpenFeature client
bool_flag = open_feature_client.get_boolean_value("bool-flag", False)
```

#### Required Targeting Key

For DevCycle SDK to work we require either a `targeting_key` or `user_id` attribute to be set on the OpenFeature context. 
This value is used to identify the user as the `user_id` property for a `DevCycleUser` in DevCycle.

### Mapping Context Properties to DevCycleUser

The provider will automatically translate known `DevCycleUser` properties from the OpenFeature context to the [`DevCycleUser`](https://github.com/DevCycleHQ/python-server-sdk/blob/main/devcycle_python_sdk/models/user.py#L8) object for use in targeting and segmentation.

For example all these properties will be set on the `DevCycleUser`:
```python
context = EvaluationContext(targeting_key="test-1234", attributes={
    "email": "test-user@domain.com",
    "name": "Test User",
    "language": "en",
    "country": "CA",
    "appVersion": "1.0.11",
    "appBuild": 1,
    "customData": {"custom": "data"},
    "privateCustomData": {"private": "data"}
})
```

Context attributes that do not map to known `DevCycleUser` properties will be automatically 
added to the `customData` dictionary of the `DevCycleUser` object.

DevCycle allows the following data types for custom data values: **boolean**, **integer**, **float**, and **str**. Other data types will be ignored

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
open_feature_client.get_object_value("json-flag", None)
```

However, these are not valid types for the DevCycle SDK, the DevCycle SDK only supports JSON Objects:
```python
# Valid JSON Object as the default value, will be evaluated by the DevCycle SDK
open_feature_client.get_object_value("json-flag", { "default": "value" })
```