import logging
import datetime
import os
import time

from devcycle_python_sdk import DevCycleLocalClient, DevCycleLocalOptions
from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.event import DevCycleEvent, EventType

VARIABLE_KEY = "test-boolean-variable"

logger = logging.getLogger(__name__)


def main():
    """
    Sample usage of the Python Server SDK using Local Bucketing.
    For a Django specific sample app, please see https://github.com/DevCycleHQ/python-django-example-app/
    """
    logging.basicConfig(level="INFO", format="%(levelname)s: %(message)s")

    # create an instance of the DevCycle Client object
    server_sdk_key = os.environ["DEVCYCLE_SERVER_SDK_KEY"]
    options = DevCycleLocalOptions()
    client = DevCycleLocalClient(server_sdk_key, options)

    # Wait for DevCycle to initialize and load the configuration
    for i in range(10):
        if client.is_initialized():
            break
        logger.info("Waiting for DevCycle to initialize...")
        time.sleep(0.5)
    else:
        logger.error("DevCycle failed to initialize")
        exit(1)

    user = DevCycleUser(user_id="test-1234", email="test-user@domain.com", country="US")

    # Use variable_value to access the value of a variable directly
    if client.variable_value(user, VARIABLE_KEY, False):
        logger.info(f"Variable {VARIABLE_KEY} is enabled")
    else:
        logger.info(f"Variable {VARIABLE_KEY} is not enabled")

    # DevCycle handles missing or wrongly typed variables by returning the default value
    # You can check this explicitly by using the variable method
    variable = client.variable(user, VARIABLE_KEY + "-does-not-exist", False)
    if variable.isDefaulted:
        logger.info(f"Variable {variable.key} is defaulted to {variable.value}")

    try:
        # Get all variables by key for user data
        all_variables_response = client.all_variables(user)
        logger.info(f"All variables:\n{all_variables_response}")

        if VARIABLE_KEY not in all_variables_response:
            logger.warning(
                f"Variable {VARIABLE_KEY} does not exist - create it in the dashboard for this example"
            )

        # Get all features by key for user data
        all_features_response = client.all_features(user)
        logger.info(f"All features:\n{all_features_response}")

        # Post a custom event to DevCycle for user
        event = DevCycleEvent(
            type=EventType.CustomEvent,
            target="some.variable.key",
            date=datetime.datetime.now(),
        )
        client.track(user, event)
    except Exception as e:
        logger.exception(f"Exception when calling DevCycle API: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
