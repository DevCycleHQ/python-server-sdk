from __future__ import print_function
from devcycle_python_sdk import Configuration, DVCClient, DVCOptions, UserData, Event
from devcycle_python_sdk.rest import ApiException
import os

def main():
    """
    Sample generic usage of the Python SDK.
    For a Django specific sample app, please see https://github.com/DevCycleHQ/python-django-example-app/

    """
    configuration = Configuration()
    configuration.api_key['Authorization'] = os.getenv('DVC_SERVER_SDK_KEY')
    options = DVCOptions(enableEdgeDB=True)

    # create an instance of the API class
    dvc = DVCClient(configuration, options)

    user = UserData(
        user_id='test',
        email='yo@yo.ca',
        country='CA'
    )
    event = Event(
        type="customEvent",
        target="somevariable.key"
    )

    try:
        # Get all features by key for user data
        api_response = dvc.all_features(user)
        print(api_response)
    except ApiException as e:
        print("Exception when calling DevcycleApi->all_features: %s\n" % e)

    variable_key = os.getenv('DVC_VARIABLE_KEY')

    try:
        # Get variable value by key for user data
        value = dvc.variable_value(user, variable_key, 'default-value')
        print(value)
    except ApiException as e:
        print("Exception when calling DevcycleApi->varaible: %s\n" % e)

    try:
        # Get variable by key for user data
        api_response = dvc.variable(user, variable_key, 'default-value')
        print(api_response)
        if not api_response.is_defaulted:
            print('NOT DEFAULTED')
    except ApiException as e:
        print("Exception when calling DevcycleApi->varaible: %s\n" % e)

    try:
        # Get variable by key for user data
        api_response_default = dvc.variable(user, variable_key+'-does-not-exist', 'default-value')
        if api_response_default.is_defaulted:
            print(api_response_default)
            print('DEFAULTED')
    except ApiException as e:
        print("Exception when calling DevcycleApi->varaible: %s\n" % e)

    try:
        # Get all variables by key for user data
        api_response = dvc.all_variables(user)
        print(api_response)
    except ApiException as e:
        print("Exception when calling DevcycleApi->all_variables: %s\n" % e)

    try:
        # Post events to DevCycle for user
        api_response = dvc.track(user, event)
        print(api_response)
    except ApiException as e:
        print("Exception when calling DevcycleApi->track: %s\n" % e)


if __name__ == "__main__":
    main()
