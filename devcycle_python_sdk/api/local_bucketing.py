import logging
import random
import time
import json

from pathlib import Path
from threading import Lock
from typing import Any, cast, Optional, List

import wasmtime
from wasmtime import (
    Engine,
    Func,
    FuncType,
    Linker,
    Memory,
    Module,
    Store,
    ValType,
)

import devcycle_python_sdk.protobuf.utils as pb_utils
import devcycle_python_sdk.protobuf.variableForUserParams_pb2 as pb2
from devcycle_python_sdk.exceptions import (
    MalformedConfigError,
)
from devcycle_python_sdk.models.bucketed_config import BucketedConfig
from devcycle_python_sdk.models.user import DevCycleUser
from devcycle_python_sdk.models.variable import Variable, determine_variable_type
from devcycle_python_sdk.models.event import FlushPayload

logger = logging.getLogger(__name__)

wasm_path = Path(__file__).parent.parent / "bucketing-lib.release.wasm"


class WASMError(Exception):
    pass


class WASMAbortError(WASMError):
    pass


class LocalBucketing:
    def __init__(self, sdk_key: str) -> None:
        self.random = random.random()
        self.wasm_lock = Lock()

        wasi_cfg = wasmtime.WasiConfig()
        wasi_cfg.inherit_env()
        wasi_cfg.inherit_stderr()
        wasi_cfg.inherit_stdout()

        wasm_engine = Engine()
        wasm_module = Module.from_file(
            wasm_engine,
            str(wasm_path),
        )
        wasm_linker = Linker(wasm_engine)
        wasm_store = Store(wasm_engine)
        wasm_store.set_wasi(wasi_cfg)
        wasm_linker.define_wasi()

        # Needs to return the current time since Epoch in milliseconds
        def __date_now_func():
            # convert from seconds to milliseconds
            return time.time() * 1000

        wasm_linker.define_func(
            "env", "Date.now", FuncType([], [ValType.f64()]), __date_now_func
        )

        def __abort_func(
            message_ptr=None,
            filename_ptr=None,
            line=0,
            column=0,
        ) -> None:
            message = None
            filename = None
            if message_ptr is not None:
                message = self._read_assembly_script_string(message_ptr)
            if filename_ptr is not None:
                filename = self._read_assembly_script_string(filename_ptr)

            raise WASMAbortError(
                f"Abort in {filename!r}:{line!r}:{column!r} -- {message!r}"
            )

        wasm_linker.define_func(
            "env",
            "abort",
            FuncType([ValType.i32(), ValType.i32(), ValType.i32(), ValType.i32()], []),
            __abort_func,
        )

        def __seed_func():
            return time.time() * random.random()

        wasm_linker.define_func(
            "env", "seed", FuncType([], [ValType.f64()]), __seed_func
        )

        def __console_log_func(message_ptr) -> None:
            message: str = self._read_assembly_script_string(message_ptr)
            logger.warning(f"DevCycle: WASM console: {message!r}")

        wasm_linker.define_func(
            "env", "console.log", FuncType([ValType.i32()], []), __console_log_func
        )

        wasm_instance = wasm_linker.instantiate(wasm_store, wasm_module)
        self.wasm_instance = wasm_instance
        self.wasm_store = wasm_store
        self.wasm_linker = wasm_linker
        self.wasm_module = wasm_module
        self.wasm_engine = wasm_engine

        wasm_memory: Memory = self._get_export("memory")
        self.wasm_memory = wasm_memory

        # Bind exported internal AssemblyScript functions
        self.__new: Func = self._get_export("__new")
        self.__pin: Func = self._get_export("__pin")
        self.__unpin: Func = self._get_export("__unpin")

        # Bind exported WASM functions
        self.initEventQueue = self._get_export("initEventQueue")
        self.flushEventQueue = self._get_export("flushEventQueue")
        self.eventQueueSize = self._get_export("eventQueueSize")
        self.onPayloadSuccess = self._get_export("onPayloadSuccess")
        self.onPayloadFailure = self._get_export("onPayloadFailure")
        self.queueEvent = self._get_export("queueEvent")
        self.queueAggregateEvent = self._get_export("queueAggregateEvent")
        self.setConfigDataUTF8 = self._get_export("setConfigDataUTF8")
        self.setPlatformDataUTF8 = self._get_export("setPlatformDataUTF8")
        self.setClientCustomDataUTF8 = self._get_export("setClientCustomDataUTF8")
        self.generateBucketedConfigForUserUTF8 = self._get_export(
            "generateBucketedConfigForUserUTF8"
        )
        self.VariableForUserProtobuf = self._get_export("variableForUser_PB")

        # Extract variable type enum values from WASM
        self.variable_type_map = {
            variable_type_key: self._get_export(
                f"VariableType.{variable_type_key}"
            ).value(wasm_store)
            for variable_type_key in [
                "Boolean",
                "String",
                "Number",
                "JSON",
            ]
        }

        # Set and pin the SDK key so it can be reused multiple times
        self.sdk_key = sdk_key
        self.sdk_key_addr = self._new_assembly_script_string(sdk_key)
        self.__pin(self.wasm_store, self.sdk_key_addr)

        # Allocate memory for header.
        object_id_uint8_array = 9
        header_pointer = cast(
            int, self.__new(self.wasm_store, 12, object_id_uint8_array)
        )

        # An external object that is not referenced from within WebAssembly
        # must be pinned whenever an allocation might happen in between
        # allocating it and passing it to WebAssembly.
        self.__pin(self.wasm_store, header_pointer)

        self._header_pointer = header_pointer

    def _get_export(self, export_name: str):
        return self.wasm_instance.exports(self.wasm_store)[export_name]

    def _new_assembly_script_string(self, param: str) -> int:
        """
        Allocate memory for a string in AssemblyScript and write the string
        into memory, then return a pointer to the string.
        Only safe for use with ASCII strings.
        """
        object_id_string = 2
        encoded = param.encode("utf-8")
        try:
            # Create pointer to string buffer in WASM memory.
            pointer = cast(
                int, self.__new(self.wasm_store, len(encoded) * 2, object_id_string)
            )
        except Exception as err:
            raise WASMError(f"Error allocating string in WASM: {err}")
        addr = pointer
        data = self.wasm_memory.data_ptr(self.wasm_store)

        # Write encoded data into buffer.
        for i, c in enumerate(encoded):
            data[addr + i * 2] = c

        return pointer

    def _read_assembly_script_string(self, pointer: int) -> str:
        """
        Read a string from AssemblyScript memory.
        Only safe for use with ASCII strings.


        """
        if pointer == 0:
            raise ValueError(
                "Null pointer passed to _read_assembly_script_string - cannot write string"
            )

        # Get a direct reference to the WASM memory
        data = self.wasm_memory.data_ptr(self.wasm_store)

        # Parse the string length from the header.
        string_length = int.from_bytes(data[pointer - 4 : pointer], byteorder="little")
        raw_data = data[pointer : pointer + string_length]

        # This skips every other index in the resulting array because there
        # isn't a great way to parse UTF-16 cleanly that matches the WTF-16
        # format that ASC uses.
        ret = bytearray(len(raw_data) // 2)
        for i in range(0, len(raw_data), 2):
            ret[i // 2] += raw_data[i]

        return ret.decode("utf-8")

    def _new_assembly_script_byte_array(self, param: bytes) -> int:
        """
        Allocates memory for a byte array in AssemblyScript and writes the byte
        array into memory, then returns a pointer to the byte array.
        """
        object_id_byte_array = 1
        data_length = len(param)
        try:
            # Allocate memory for buffer.
            buffer_pointer = cast(
                int, self.__new(self.wasm_store, data_length, object_id_byte_array)
            )

            # Get a direct reference to the WASM memory
            data = self.wasm_memory.data_ptr(self.wasm_store)

            # Write the buffer pointer value into the first 4 bytes of the header, little endian.
            for i, b in enumerate(buffer_pointer.to_bytes(4, byteorder="little")):
                data[self._header_pointer + i] = b
                data[self._header_pointer + i + 4] = b

            little_endian_buffer_len = data_length.to_bytes(4, byteorder="little")

            # Write the buffer length into bytes 8-12 of the header, little endian.
            for i, b in enumerate(little_endian_buffer_len):
                data[self._header_pointer + 8 + i] = b

            # Write the byte array data into the WASM buffer.
            for i, b in enumerate(param):
                data[buffer_pointer + i] = b

            return self._header_pointer
        except Exception as err:
            raise WASMError(f"Error writing byte array to WASM: {err}")

    def _read_assembly_script_byte_array(self, pointer: int) -> bytes:
        """
        Read a byte array from AssemblyScript memory.
        """
        if pointer == 0:
            raise ValueError(
                "Null pointer passed to _read_assembly_script_byte_array - cannot write string"
            )

        # Get a direct reference to the WASM memory
        data = self.wasm_memory.data_ptr(self.wasm_store)

        # Parse the data length and data pointer from the header.
        data_length = int.from_bytes(
            data[pointer + 8 : pointer + 12], byteorder="little"
        )
        data_pointer = int.from_bytes(data[pointer : pointer + 4], byteorder="little")

        ret = bytearray(data_length)

        # Copy the data from the WASM buffer into the return value.
        for i in range(data_length):
            ret[i] = data[data_pointer + i]

        return bytes(ret)

    def init_event_queue(self, client_uuid, options_json: str) -> None:
        with self.wasm_lock:
            client_uuid_addr = self._new_assembly_script_string(client_uuid)
            options_addr = self._new_assembly_script_string(options_json)
            self.initEventQueue(
                self.wasm_store, self.sdk_key_addr, client_uuid_addr, options_addr
            )

    def get_variable_for_user_protobuf(
        self, user: DevCycleUser, key: str, default_value: Any
    ) -> Optional[Variable]:
        var_type = determine_variable_type(default_value)
        pb_variable_type = pb_utils.convert_type_enum_to_variable_type(var_type)

        params_pb = pb2.VariableForUserParams_PB(
            sdkKey=self.sdk_key,
            variableKey=key,
            variableType=pb_variable_type,
            user=pb_utils.create_dvcuser_pb(user),
            shouldTrackEvent=True,
        )

        params_str = params_pb.SerializeToString()

        with self.wasm_lock:
            params_addr = self._new_assembly_script_byte_array(params_str)
            variable_addr = self.VariableForUserProtobuf(self.wasm_store, params_addr)

            if variable_addr == 0:
                return None
            else:
                var_bytes = self._read_assembly_script_byte_array(variable_addr)
                sdk_variable = pb2.SDKVariable_PB()
                sdk_variable.ParseFromString(var_bytes)

                return pb_utils.create_variable(sdk_variable, default_value)

    def generate_bucketed_config(self, user: DevCycleUser) -> BucketedConfig:
        user_json = json.dumps(user.to_json())

        with self.wasm_lock:
            user_json_addr = self._new_assembly_script_byte_array(
                user_json.encode("utf-8")
            )
            config_addr = self.generateBucketedConfigForUserUTF8(
                self.wasm_store, self.sdk_key_addr, user_json_addr
            )

            config_bytes = self._read_assembly_script_byte_array(config_addr)

            config_data = json.loads(config_bytes.decode("utf-8"))

            try:
                config = BucketedConfig.from_json(config_data)
            except KeyError as e:
                raise MalformedConfigError(
                    f"Failed to parse bucketed config: missing key {e}"
                ) from e

            config.user = user

            return config

    def store_config(self, config_json: str) -> None:
        with self.wasm_lock:
            data = config_json.encode("utf-8")
            config_addr = self._new_assembly_script_byte_array(data)
            self.setConfigDataUTF8(self.wasm_store, self.sdk_key_addr, config_addr)

    def set_platform_data(self, platform_json: str) -> None:
        with self.wasm_lock:
            data = platform_json.encode("utf-8")
            data_addr = self._new_assembly_script_byte_array(data)
            self.setPlatformDataUTF8(self.wasm_store, data_addr)

    def set_client_custom_data(self, client_data_json: str) -> None:
        with self.wasm_lock:
            data = client_data_json.encode("utf-8")
            data_addr = self._new_assembly_script_byte_array(data)
            self.setClientCustomDataUTF8(self.wasm_store, self.sdk_key_addr, data_addr)

    def flush_event_queue(self) -> List[FlushPayload]:
        """
        Collects the events that are ready to send to the server. Events are group into separate payloads

        Returns: a list of FlushPayload objects, or an empty list if there are no events to send
        """
        with self.wasm_lock:
            result_addr = self.flushEventQueue(self.wasm_store, self.sdk_key_addr)
            result_str = self._read_assembly_script_string(result_addr)
            result_json = json.loads(result_str)
            return [FlushPayload.from_json(element) for element in result_json]

    def on_event_payload_success(self, payload_id: str) -> None:
        """
        Notifies the WASM that the events associated with the payload_id have been sent successfully and
        can be purged from the queue
        """
        with self.wasm_lock:
            id_addr = self._new_assembly_script_string(payload_id)
            self.onPayloadSuccess(self.wasm_store, self.sdk_key_addr, id_addr)

    def on_event_payload_failure(self, payload_id: str, retryable: bool) -> None:
        """
        Notifies the WASM that the events associated with the payload_id failed to be sent and should
        be re-queued.
        """
        with self.wasm_lock:
            id_addr = self._new_assembly_script_string(payload_id)
            self.onPayloadFailure(
                self.wasm_store, self.sdk_key_addr, id_addr, 1 if retryable else 0
            )

    def get_event_queue_size(self) -> int:
        """
        Returns the number of events currently in the queue
        """
        with self.wasm_lock:
            val = self.eventQueueSize(self.wasm_store, self.sdk_key_addr)
            return int(val)

    def queue_event(self, user_json: str, event_json: str) -> None:
        with self.wasm_lock:
            user_addr = self._new_assembly_script_string(user_json)
            event_addr = self._new_assembly_script_string(event_json)
            self.queueEvent(self.wasm_store, self.sdk_key_addr, user_addr, event_addr)

    def queue_aggregate_event(
        self, event_json: str, variable_variation_map_json: str
    ) -> None:
        with self.wasm_lock:
            event_addr = self._new_assembly_script_string(event_json)
            variable_variation_map_addr = self._new_assembly_script_string(
                variable_variation_map_json
            )
            self.queueAggregateEvent(
                self.wasm_store,
                self.sdk_key_addr,
                event_addr,
                variable_variation_map_addr,
            )
