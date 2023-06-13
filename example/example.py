import logging
import os

from devcycle_python_sdk import DevCycleCloudClient, DevCycleCloudOptions
from devcycle_python_sdk.models.user import User
from devcycle_python_sdk.models.event import Event

VARIABLE_KEY = "test-boolean-variable"

logger = logging.getLogger(__name__)


def main():
    """
    Sample generic usage of the Python SDK.
    For a Django specific sample app, please see https://github.com/DevCycleHQ/python-django-example-app/

    """
    logging.basicConfig(level="INFO", format="%(levelname)s: %(message)s")

    options = DevCycleCloudOptions(enable_edge_db=True)

    # create an instance of the API class
    server_sdk_key = os.environ["DVC_SERVER_SDK_KEY"]
    dvc = DevCycleCloudClient(server_sdk_key, options)

    user = User(user_id="test", email="yo@yo.ca", country="CA")
    event = Event(type="customEvent", target="somevariable.key")

    # Use variable_value to access the value of a variable directly
    if dvc.variable_value(user, VARIABLE_KEY, False):
        logger.info(f"Variable {VARIABLE_KEY} is enabled")
    else:
        logger.info(f"Variable {VARIABLE_KEY} is not enabled")

    # DevCycle handles missing or wrongly typed variables by returning the default value
    # You can check this explicitly by using the variable method
    variable = dvc.variable(user, VARIABLE_KEY + "-does-not-exist", False)
    if variable.isDefaulted:
        logger.info(f"Variable {variable.key} is defaulted to {variable.value}")

    try:
        # Get all variables by key for user data
        all_variables_response = dvc.all_variables(user)
        logger.info("All variables:\n%s", all_variables_response)

        if VARIABLE_KEY not in all_variables_response:
            logger.warning(
                f"Variable {VARIABLE_KEY} does not exist - create it in the dashboard for this example"
            )

        # Get all features by key for user data
        all_features_response = dvc.all_features(user)
        logger.info("All features:\n%s", all_features_response)

        # Post events to DevCycle for user
        track_response = dvc.track(user, event)
        logger.info(track_response)
    except Exception as e:
        logger.exception("Exception when calling Devcycle API: %s\n" % e)


if __name__ == "__main__":
    main()
