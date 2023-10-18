import logging
import time
import os

from devcycle_python_sdk import DevCycleLocalClient, DevCycleLocalOptions
from devcycle_python_sdk.openfeature.provider import DevCycleProvider

from openfeature import api
from openfeature.evaluation_context import EvaluationContext

FLAG_KEY = "test-boolean-variable"

logger = logging.getLogger(__name__)


def main():
    """
    Sample usage of the DevCycle OpenFeature Provider along with the Python Server SDK using Local Bucketing.
    """
    logging.basicConfig(level="INFO", format="%(levelname)s: %(message)s")

    # create an instance of the DevCycle Client object
    server_sdk_key = os.environ["DEVCYCLE_SERVER_SDK_KEY"]
    devcycle_client = DevCycleLocalClient(server_sdk_key, DevCycleLocalOptions())

    # Wait for DevCycle to initialize and load the configuration
    for i in range(10):
        if devcycle_client.is_initialized():
            break
        logger.info("Waiting for DevCycle to initialize...")
        time.sleep(0.5)
    else:
        logger.error("DevCycle failed to initialize")
        exit(1)

    # set the provider for OpenFeature
    api.set_provider(DevCycleProvider(devcycle_client))

    # get the OpenFeature client
    open_feature_client = api.get_client()

    # create the request context for the user
    context = EvaluationContext(
        targeting_key="test-1234",
        attributes={"email": "test-user@domain.com", "country": "US"},
    )

    # Look up the value of the flag
    if open_feature_client.get_boolean_value(FLAG_KEY, False, context):
        logger.info(f"Variable {FLAG_KEY} is enabled")
    else:
        logger.info(f"Variable {FLAG_KEY} is not enabled")

    devcycle_client.close()


if __name__ == "__main__":
    main()
