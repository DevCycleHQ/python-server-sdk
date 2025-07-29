import json
import logging
import unittest
import uuid

from devcycle_python_sdk.api.local_bucketing import LocalBucketing, WASMAbortError
from devcycle_python_sdk.models.bucketed_config import (
    Environment,
    FeatureVariation,
    Project,
    ProjectSettings,
)
from devcycle_python_sdk.models.eval_reason import EvalReason
from devcycle_python_sdk.models.feature import Feature
from devcycle_python_sdk.models.variable import Variable
from devcycle_python_sdk.models.platform_data import default_platform_data
from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.event import DevCycleEvent, EventType
from devcycle_python_sdk.models.variable import TypeEnum
from test.fixture.data import small_config, large_config, special_character_config

logger = logging.getLogger(__name__)


class LocalBucketingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.test_sdk_key = "dvc_server_testkey"
        self.local_bucketing = LocalBucketing(self.test_sdk_key)
        self.client_uuid = str(uuid.uuid4())

    def test_init(self):
        local_bucketing = LocalBucketing(self.test_sdk_key)
        self.assertIsNotNone(local_bucketing)

    def test_write_read_string(self) -> None:
        # Test that we can safely pass ASCII strings to the WASM module and read them back
        test_string = "test_bytes"
        arg_pointer = self.local_bucketing._new_assembly_script_string(test_string)

        echo_func = self.local_bucketing._get_export("echoString")

        result_pointer = echo_func(self.local_bucketing.wasm_store, arg_pointer)

        result_bytes = self.local_bucketing._read_assembly_script_string(result_pointer)
        self.assertEqual(result_bytes, test_string)

    def test_write_read_bytes_array(self) -> None:
        # Test that we can safely pass byte arrays to the WASM module and read them back
        test_bytes = "test_bytes".encode("utf-8")
        arg_pointer = self.local_bucketing._new_assembly_script_byte_array(test_bytes)

        echo_func = self.local_bucketing._get_export("echoUint8Array")

        result_pointer = echo_func(self.local_bucketing.wasm_store, arg_pointer)

        result_bytes = self.local_bucketing._read_assembly_script_byte_array(
            result_pointer
        )
        self.assertEqual(result_bytes, test_bytes)

    def test_abort(self) -> None:
        abort_func = self.local_bucketing._get_export("triggerAbort")

        with self.assertRaises(WASMAbortError) as context:
            abort_func(self.local_bucketing.wasm_store)

        self.assertRegex(
            context.exception.args[0],
            r"Abort in '[^']+':[0-9]+:[0-9]+ -- 'Manual abort triggered'",
        )

    def test_store_config(self) -> None:
        # should store each config with any errors
        self.local_bucketing.store_config(small_config())
        self.local_bucketing.store_config(large_config())
        self.local_bucketing.store_config(special_character_config())

    def test_set_platform_data(self):
        # should set the data without any errors
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)

    def test_set_client_custom_data(self):
        # should set the data without any errors
        client_custom_data = {
            "strProp": "strVal",
            "intProp": 1,
            "floatProp": 1.1,
            "boolProp": True,
            "nullProp": None,
        }
        data_str = json.dumps(client_custom_data)
        self.local_bucketing.set_client_custom_data(data_str)

    def test_get_variable_for_user_protobuf(self):
        self.local_bucketing.store_config(small_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)
        self.local_bucketing.init_event_queue(self.client_uuid, "{}")
        user = DevCycleUser(user_id="test_user_id")
        result = self.local_bucketing.get_variable_for_user_protobuf(
            user=user, key="string-var", default_value="default value"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.key, "string-var")
        self.assertEqual(result.type, TypeEnum.STRING)
        self.assertEqual(result.value, "variationOn")
        self.assertFalse(result.isDefaulted)

    def test_get_variable_for_user_protobuf_special_characters(self):
        self.local_bucketing.store_config(special_character_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)
        self.local_bucketing.init_event_queue(self.client_uuid, "{}")
        user = DevCycleUser(user_id="test_user_id")
        result = self.local_bucketing.get_variable_for_user_protobuf(
            user=user, key="string-var", default_value="default value"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.key, "string-var")
        self.assertEqual(result.type, TypeEnum.STRING)
        self.assertEqual(result.value, "öé 🐍 ¥ variationOn")
        self.assertFalse(result.isDefaulted)

    def test_get_variable_for_user_protobuf_type_mismatch(self):
        self.local_bucketing.store_config(small_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)
        self.local_bucketing.init_event_queue(self.client_uuid, "{}")
        user = DevCycleUser(user_id="test_user_id")

        # type mismatch is handled inside the WASM and will return
        # no data if the type is not correct
        result = self.local_bucketing.get_variable_for_user_protobuf(
            user=user, key="string-var", default_value=9999
        )
        self.assertIsNone(result)

    def test_generate_bucketed_config(self):
        self.local_bucketing.store_config(small_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)
        self.local_bucketing.init_event_queue(self.client_uuid, "{}")
        user = DevCycleUser(user_id="test_user_id")

        result = self.local_bucketing.generate_bucketed_config(user=user)

        expected_features = {
            "a-cool-new-feature": Feature(
                _id="62fbf6566f1ba302829f9e32",
                key="a-cool-new-feature",
                type="release",
                _variation="62fbf6566f1ba302829f9e39",
                variationName="VariationOn",
                variationKey="variation-on",
                evalReason=None,
            )
        }
        expected_eval = EvalReason(
            reason="TARGETING_MATCH",
            details="All Users",
            target_id="63125321d31c601f992288bc",
        )
        expected_variables = {
            "a-cool-new-feature": Variable(
                _id="62fbf6566f1ba302829f9e34",
                key="a-cool-new-feature",
                type="Boolean",
                value=True,
                isDefaulted=None,
                defaultValue=None,
                evalReason=None,
                eval=expected_eval,
            ),
            "string-var": Variable(
                _id="63125320a4719939fd57cb2b",
                key="string-var",
                type="String",
                value="variationOn",
                isDefaulted=None,
                defaultValue=None,
                evalReason=None,
                eval=expected_eval,
            ),
            "json-var": Variable(
                _id="64372363125123fca69d3f7b",
                key="json-var",
                type="JSON",
                value={
                    "displayText": "This variation is on",
                    "showDialog": True,
                    "maxUsers": 100,
                },
                isDefaulted=None,
                defaultValue=None,
                evalReason=None,
                eval=expected_eval,
            ),
            "num-var": Variable(
                _id="65272363125123fca69d3a7d",
                key="num-var",
                type="Number",
                value=12345,
                isDefaulted=None,
                defaultValue=None,
                evalReason=None,
                eval=expected_eval,
            ),
            "float-var": Variable(
                _id="61200363125123fca69d3a7a",
                key="float-var",
                type="Number",
                value=3.14159,
                isDefaulted=None,
                defaultValue=None,
                evalReason=None,
                eval=expected_eval,
            ),
        }

        self.assertIsNotNone(result)
        self.assertEqual(result.user, user)
        self.assertEqual(
            Project(
                id="61f97628ff4afcb6d057dbf0",
                key="emma-project",
                a0_organization="org_tPyJN5dvNNirKar7",
                settings=ProjectSettings(
                    edge_db=None, opt_in=None, disable_passthrough_rollouts=False
                ),
            ),
            result.project,
        )
        self.assertEqual(
            result.environment,
            Environment(id="61f97628ff4afcb6d057dbf2", key="development"),
        )
        self.assertEqual(
            result.features,
            expected_features,
        )
        self.assertEqual(
            result.feature_variation_map,
            {"62fbf6566f1ba302829f9e32": "62fbf6566f1ba302829f9e39"},
        )
        self.assertEqual(
            result.variable_variation_map,
            {
                "a-cool-new-feature": FeatureVariation(
                    feature="62fbf6566f1ba302829f9e32",
                    variation="62fbf6566f1ba302829f9e39",
                ),
                "string-var": FeatureVariation(
                    feature="62fbf6566f1ba302829f9e32",
                    variation="62fbf6566f1ba302829f9e39",
                ),
                "json-var": FeatureVariation(
                    feature="62fbf6566f1ba302829f9e32",
                    variation="62fbf6566f1ba302829f9e39",
                ),
                "num-var": FeatureVariation(
                    feature="62fbf6566f1ba302829f9e32",
                    variation="62fbf6566f1ba302829f9e39",
                ),
                "float-var": FeatureVariation(
                    feature="62fbf6566f1ba302829f9e32",
                    variation="62fbf6566f1ba302829f9e39",
                ),
            },
        )
        self.assertEqual(
            result.variables,
            expected_variables,
        )
        self.assertEqual(result.known_variable_keys, [])

    def test_get_event_queue_size(self):
        self.local_bucketing.store_config(small_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)
        self.local_bucketing.init_event_queue(self.client_uuid, "{}")

        result = self.local_bucketing.get_event_queue_size()
        self.assertEqual(result, 0)

    def test_flush_event_queue_empty(self):
        self.local_bucketing.store_config(small_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)

        self.local_bucketing.init_event_queue(
            self.client_uuid,
            json.dumps(
                {
                    "disableAutomaticEventLogging": False,
                    "disableCustomEventLogging": False,
                    "minEventsPerFlush": 1,
                }
            ),
        )
        results = self.local_bucketing.flush_event_queue()
        self.assertIsNotNone(results)
        self.assertListEqual(results, [])

    def test_flush_event_queue(self):
        self.local_bucketing.store_config(small_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)

        self.local_bucketing.init_event_queue(
            self.client_uuid,
            json.dumps(
                {
                    "disableAutomaticEventLogging": False,
                    "disableCustomEventLogging": False,
                    "minEventsPerFlush": 1,
                }
            ),
        )

        # trigger two events for a single user
        user = DevCycleUser(user_id="test_user_id")
        self.local_bucketing.get_variable_for_user_protobuf(
            user=user, key="string-var", default_value="default value"
        )
        self.local_bucketing.get_variable_for_user_protobuf(
            user=user, key="bool-var", default_value=False
        )
        results = self.local_bucketing.flush_event_queue()
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].eventCount, 2)
        self.assertIsNotNone(results[0].payloadId)
        self.assertTrue(len(results[0].payloadId) > 0)
        self.assertEqual(len(results[0].records), 1)
        self.assertEqual(len(results[0].records[0].events), 2)

    def test_on_event_payload_failure_unknown_payload_id(self):
        self.local_bucketing.store_config(small_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)

        self.local_bucketing.init_event_queue(
            self.client_uuid,
            json.dumps(
                {
                    "disableAutomaticEventLogging": False,
                    "disableCustomEventLogging": False,
                    "minEventsPerFlush": 1,
                }
            ),
        )

        with self.assertRaises(WASMAbortError):
            self.local_bucketing.on_event_payload_failure("test_payload_id", True)

    def test_on_event_payload_success_unknown_payload_id(self):
        self.local_bucketing.store_config(small_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)

        self.local_bucketing.init_event_queue(
            self.client_uuid,
            json.dumps(
                {
                    "disableAutomaticEventLogging": False,
                    "disableCustomEventLogging": False,
                    "minEventsPerFlush": 1,
                }
            ),
        )

        with self.assertRaises(WASMAbortError):
            self.local_bucketing.on_event_payload_success("test_payload_id")

    def test_queue_event(self):
        self.local_bucketing.store_config(small_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)
        self.local_bucketing.init_event_queue(self.client_uuid, "{}")
        user = DevCycleUser(user_id="test_user_id")
        event = DevCycleEvent(
            type=EventType.CustomEvent,
            target="string-var",
            value=1,
            metaData={"test": "test"},
        )
        user_json = json.dumps(user.to_json())
        event_json = json.dumps(event.to_json())
        self.local_bucketing.queue_event(user_json, event_json)

    def test_queue_aggregate_event(self):
        self.local_bucketing.store_config(small_config())
        platform_json = json.dumps(default_platform_data().to_json())
        self.local_bucketing.set_platform_data(platform_json)
        self.local_bucketing.init_event_queue(self.client_uuid, "{}")

        event = DevCycleEvent(
            type=EventType.AggVariableDefaulted,
            target="string-var",
            value=1,
            metaData={"test": "test"},
        )
        event_json = json.dumps(event.to_json())
        variable_variation_map_json = "{}"
        self.local_bucketing.queue_aggregate_event(
            event_json, variable_variation_map_json
        )


if __name__ == "__main__":
    unittest.main()
