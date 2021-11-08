# devcycle_python_sdk.DevcycleApi

All URIs are relative to *https://bucketing-api.devcycle.com/*

Method | HTTP request | Description
------------- | ------------- | -------------
[**get_features**](DevcycleApi.md#get_features) | **POST** /v1/features | Get all features by key for user data
[**get_variable_by_key**](DevcycleApi.md#get_variable_by_key) | **POST** /v1/variables/{key} | Get variable by key for user data
[**get_variables**](DevcycleApi.md#get_variables) | **POST** /v1/variables | Get all variables by key for user data
[**post_events**](DevcycleApi.md#post_events) | **POST** /v1/track | Post events to DevCycle for user

# **get_features**
> dict(str, Feature) get_features(body)

Get all features by key for user data

### Example
```python
from __future__ import print_function
import time
import devcycle_python_sdk
from devcycle_python_sdk.rest import ApiException
from pprint import pprint

# Configure API key authorization: bearerAuth
configuration = devcycle_python_sdk.Configuration()
configuration.api_key['Authorization'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Authorization'] = 'Bearer'

# create an instance of the API class
api_instance = devcycle_python_sdk.DevcycleApi(devcycle_python_sdk.ApiClient(configuration))
body = devcycle_python_sdk.UserData() # UserData | 

try:
    # Get all features by key for user data
    api_response = api_instance.get_features(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevcycleApi->get_features: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**UserData**](UserData.md)|  | 

### Return type

[**dict(str, Feature)**](Feature.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_variable_by_key**
> Variable get_variable_by_key(body, key)

Get variable by key for user data

### Example
```python
from __future__ import print_function
import time
import devcycle_python_sdk
from devcycle_python_sdk.rest import ApiException
from pprint import pprint

# Configure API key authorization: bearerAuth
configuration = devcycle_python_sdk.Configuration()
configuration.api_key['Authorization'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Authorization'] = 'Bearer'

# create an instance of the API class
api_instance = devcycle_python_sdk.DevcycleApi(devcycle_python_sdk.ApiClient(configuration))
body = devcycle_python_sdk.UserData() # UserData | 
key = 'key_example' # str | Variable key

try:
    # Get variable by key for user data
    api_response = api_instance.get_variable_by_key(body, key)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevcycleApi->get_variable_by_key: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**UserData**](UserData.md)|  | 
 **key** | **str**| Variable key | 

### Return type

[**Variable**](Variable.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **get_variables**
> dict(str, Variable) get_variables(body)

Get all variables by key for user data

### Example
```python
from __future__ import print_function
import time
import devcycle_python_sdk
from devcycle_python_sdk.rest import ApiException
from pprint import pprint

# Configure API key authorization: bearerAuth
configuration = devcycle_python_sdk.Configuration()
configuration.api_key['Authorization'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Authorization'] = 'Bearer'

# create an instance of the API class
api_instance = devcycle_python_sdk.DevcycleApi(devcycle_python_sdk.ApiClient(configuration))
body = devcycle_python_sdk.UserData() # UserData | 

try:
    # Get all variables by key for user data
    api_response = api_instance.get_variables(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevcycleApi->get_variables: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**UserData**](UserData.md)|  | 

### Return type

[**dict(str, Variable)**](Variable.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

# **post_events**
> InlineResponse200 post_events(body)

Post events to DevCycle for user

### Example
```python
from __future__ import print_function
import time
import devcycle_python_sdk
from devcycle_python_sdk.rest import ApiException
from pprint import pprint

# Configure API key authorization: bearerAuth
configuration = devcycle_python_sdk.Configuration()
configuration.api_key['Authorization'] = 'YOUR_API_KEY'
# Uncomment below to setup prefix (e.g. Bearer) for API key, if needed
# configuration.api_key_prefix['Authorization'] = 'Bearer'

# create an instance of the API class
api_instance = devcycle_python_sdk.DevcycleApi(devcycle_python_sdk.ApiClient(configuration))
body = devcycle_python_sdk.UserDataAndEventBody() # UserDataAndEventBody | 

try:
    # Post events to DevCycle for user
    api_response = api_instance.post_events(body)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling DevcycleApi->post_events: %s\n" % e)
```

### Parameters

Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **body** | [**UserDataAndEventBody**](UserDataAndEventBody.md)|  | 

### Return type

[**InlineResponse200**](InlineResponse200.md)

### Authorization

[bearerAuth](../README.md#bearerAuth)

### HTTP request headers

 - **Content-Type**: application/json
 - **Accept**: application/json

[[Back to top]](#) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to Model list]](../README.md#documentation-for-models) [[Back to README]](../README.md)

