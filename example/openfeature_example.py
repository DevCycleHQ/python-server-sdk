import logging
import time
import os

from devcycle_python_sdk import DevCycleLocalClient, DevCycleLocalOptions

from openfeature import api
from openfeature.evaluation_context import EvaluationContext

logger = logging.getLogger(__name__)


def main():
    """
    Sample usage of the DevCycle OpenFeature Provider along with the Python Server SDK using Local Bucketing.

    This example demonstrates how to use all variable types supported by DevCycle through OpenFeature:
    - Boolean variables
    - String variables
    - Number variables (integer and float)
    - JSON object variables

    See DEVCYCLE_SETUP.md for instructions on creating the required variables in DevCycle.
    """
    logging.basicConfig(level="INFO", format="%(levelname)s: %(message)s")

    # create an instance of the DevCycle Client object
    server_sdk_key = os.environ.get("DEVCYCLE_SERVER_SDK_KEY")
    if not server_sdk_key:
        logger.error("DEVCYCLE_SERVER_SDK_KEY environment variable is not set")
        logger.error(
            "Please set it with: export DEVCYCLE_SERVER_SDK_KEY='your-sdk-key'"
        )
        exit(1)

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

    logger.info("DevCycle initialized successfully!\n")

    # set the provider for OpenFeature
    api.set_provider(devcycle_client.get_openfeature_provider())

    # get the OpenFeature client
    open_feature_client = api.get_client()

    # create the request context for the user
    context = EvaluationContext(
        targeting_key="test-1234",
        attributes={
            "email": "test-user@domain.com",
            "name": "Test User",
            "language": "en",
            "country": "CA",
            "appVersion": "1.0.11",
            "appBuild": 1000,
            "customData": {"custom": "data"},
            "privateCustomData": {"private": "data"},
        },
    )

    logger.info("=" * 60)
    logger.info("Testing Boolean Variable")
    logger.info("=" * 60)

    # Test Boolean Variable
    boolean_details = open_feature_client.get_boolean_details(
        "test-boolean-variable", False, context
    )
    logger.info("Variable Key: test-boolean-variable")
    logger.info("Value: {boolean_details.value}")
    logger.info("Reason: {boolean_details.reason}")
    if boolean_details.value:
        logger.info("✓ Boolean variable is ENABLED")
    else:
        logger.info("✗ Boolean variable is DISABLED")

    logger.info("\n" + "=" * 60)
    logger.info("Testing String Variable")
    logger.info("=" * 60)

    # Test String Variable
    open_feature_client.get_string_details(
        "test-string-variable", "default string", context
    )
    logger.info("Variable Key: test-string-variable")
    logger.info("Value: {string_details.value}")
    logger.info("Reason: {string_details.reason}")

    logger.info("\n" + "=" * 60)
    logger.info("Testing Number Variable (Integer)")
    logger.info("=" * 60)

    # Test Number Variable (Integer)
    open_feature_client.get_integer_details("test-number-variable", 0, context)
    logger.info("Variable Key: test-number-variable")
    logger.info("Value: {integer_details.value}")
    logger.info("Reason: {integer_details.reason}")

    logger.info("\n" + "=" * 60)
    logger.info("Testing Number Variable (Float)")
    logger.info("=" * 60)

    # Test Number Variable as Float
    # Note: If the DevCycle variable is an integer, it will be cast to float
    open_feature_client.get_float_value("test-number-variable", 0.0, context)
    logger.info("Variable Key: test-number-variable (as float)")
    logger.info("Value: {float_value}")

    logger.info("\n" + "=" * 60)
    logger.info("Testing JSON Object Variable")
    logger.info("=" * 60)

    # Test JSON Object Variable
    open_feature_client.get_object_details(
        "test-json-variable", {"default": "value"}, context
    )
    logger.info("Variable Key: test-json-variable")
    logger.info("Value: {json_details.value}")
    logger.info("Reason: {json_details.reason}")

    logger.info("\n" + "=" * 60)
    logger.info("Testing Object Variable - Empty Dictionary")
    logger.info("=" * 60)

    # Test with empty dictionary default (valid per OpenFeature spec)
    open_feature_client.get_object_value("test-json-variable", {}, context)
    logger.info("Variable Key: test-json-variable (with empty default)")
    logger.info("Value: {empty_dict_result}")

    logger.info("\n" + "=" * 60)
    logger.info("Testing Object Variable - Mixed Types")
    logger.info("=" * 60)

    # Test with flat dictionary containing mixed primitive types
    # OpenFeature allows string, int, float, bool, and None in flat dictionaries
    mixed_default = {
        "string_key": "hello",
        "int_key": 42,
        "float_key": 3.14,
        "bool_key": True,
        "none_key": None,
    }
    mixed_result = open_feature_client.get_object_value(
        "test-json-variable", mixed_default, context
    )
    logger.info("Variable Key: test-json-variable (with mixed types)")
    logger.info("Value: {mixed_result}")
    logger.info(
        f"Value types: {[(k, type(v).__name__) for k, v in mixed_result.items()]}"
    )

    logger.info("\n" + "=" * 60)
    logger.info("Testing Object Variable - All String Values")
    logger.info("=" * 60)

    # Test with all string values
    string_dict_default = {
        "name": "John Doe",
        "email": "john@example.com",
        "status": "active",
    }
    open_feature_client.get_object_value(
        "test-json-variable", string_dict_default, context
    )
    logger.info("Variable Key: test-json-variable (all strings)")
    logger.info("Value: {string_dict_result}")

    logger.info("\n" + "=" * 60)
    logger.info("Testing Object Variable - Numeric Values")
    logger.info("=" * 60)

    # Test with numeric values (integers and floats)
    numeric_dict_default = {"count": 100, "percentage": 85.5, "threshold": 0}
    open_feature_client.get_object_value(
        "test-json-variable", numeric_dict_default, context
    )
    logger.info("Variable Key: test-json-variable (numeric)")
    logger.info("Value: {numeric_dict_result}")

    logger.info("\n" + "=" * 60)
    logger.info("Testing Object Variable - Boolean Flags")
    logger.info("=" * 60)

    # Test with boolean values
    bool_dict_default = {"feature_a": True, "feature_b": False, "feature_c": True}
    open_feature_client.get_object_value(
        "test-json-variable", bool_dict_default, context
    )
    logger.info("Variable Key: test-json-variable (booleans)")
    logger.info("Value: {bool_dict_result}")

    logger.info("\n" + "=" * 60)
    logger.info("Testing Object Variable - With None Values")
    logger.info("=" * 60)

    # Test with None values (valid per OpenFeature spec for flat dictionaries)
    none_dict_default = {
        "optional_field": None,
        "required_field": "value",
        "nullable_count": None,
    }
    open_feature_client.get_object_value(
        "test-json-variable", none_dict_default, context
    )
    logger.info("Variable Key: test-json-variable (with None)")
    logger.info("Value: {none_dict_result}")

    logger.info("\n" + "=" * 60)
    logger.info("Testing Non-Existent Variable (Should Return Default)")
    logger.info("=" * 60)

    # Test non-existent variable to demonstrate default handling
    open_feature_client.get_string_details(
        "doesnt-exist", "default fallback value", context
    )
    logger.info("Variable Key: doesnt-exist")
    logger.info("Value: {nonexistent_details.value}")
    logger.info("Reason: {nonexistent_details.reason}")

    logger.info("\n" + "=" * 60)
    logger.info("All tests completed!")
    logger.info("=" * 60)

    devcycle_client.close()


if __name__ == "__main__":
    main()
