from __future__ import print_function
from devcycle_python_sdk import Configuration, DVCClient, UserData, Event, Variable
from devcycle_python_sdk.rest import ApiException
def main():

    configuration = Configuration()
    configuration.api_key['Authorization'] = 'server-1bf0c139-6861-41e1-8d2d-ea0416045f99'


    # create an instance of the API class
    dvc = DVCClient(configuration)

    user = UserData(
        user_id='test',
        email='yo@yo.ca',
        country='CA'
    )
    variable = Variable(value='test', is_defaulted=True, key='test')
    print('test varia')
    print(variable)
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

    key = 'elliot-test' # str | Variable key

    try:
        # Get variable by key for user data
        api_response = dvc.variable(user, key, 'default-value')
        print(api_response)
        if not api_response.is_defaulted:
            print('NOT DEFAULTED')
    except ApiException as e:
        print("Exception when calling DevcycleApi->varaible: %s\n" % e)

    try:
        # Get variable by key for user data
        api_response_default = dvc.variable(user, 'elliot-etakjhsd', 'default-value')
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
