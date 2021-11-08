# UserData

## Properties
Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**user_id** | **str** | Unique id to identify the user | 
**email** | **str** | User&#x27;s email used to identify the user on the dashaboard / target audiences | [optional] 
**name** | **str** | User&#x27;s name used to idenify the user on the dashaboard / target audiences | [optional] 
**language** | **str** | User&#x27;s language in ISO 639-1 format | [optional] 
**country** | **str** | User&#x27;s country in ISO 3166 alpha-2 format | [optional] 
**app_version** | **str** | App Version of the running application | [optional] 
**app_build** | **str** | App Build number of the running application | [optional] 
**custom_data** | **object** | User&#x27;s custom data to target the user with, data will be logged to DevCycle for use in dashboard. | [optional] 
**private_custom_data** | **object** | User&#x27;s custom data to target the user with, data will not be logged to DevCycle only used for feature bucketing. | [optional] 
**created_date** | **float** | Date the user was created, Unix epoch timestamp format | [optional] 
**last_seen_date** | **float** | Date the user was created, Unix epoch timestamp format | [optional] 
**platform** | **str** | Platform the Client SDK is running on | [optional] 
**platform_version** | **str** | Version of the platform the Client SDK is running on | [optional] 
**device_type** | **str** | User&#x27;s device type | [optional] 
**sdk_type** | **str** | DevCycle SDK type | [optional] 
**sdk_version** | **str** | DevCycle SDK Version | [optional] 

[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)

