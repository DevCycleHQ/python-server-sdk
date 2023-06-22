import logging
import random
import time
from pathlib import Path
from threading import Lock

import wasmtime
from wasmtime import (
    Store,
    Module,
    Linker,
    FuncType,
    Engine,
    ValType,
)

logger = logging.getLogger(__name__)

wasm_path = Path(__file__).parent.parent / "bucketing-lib.debug.wasm"


class WASMError(Exception):
    pass


class WASMAbortError(WASMError):
    pass


class LocalBucketing:
    def __init__(self, sdk_key: str) -> None:
        self.random = random.random()
        self.wasm_mutex = Lock()
        self.flush_mutex = Lock()

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

        def __date_now_func():
            return time.time()

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
            logger.warning(f"WASM console: {message!r}")

        wasm_linker.define_func(
            "env", "console.log", FuncType([ValType.i32()], []), __console_log_func
        )

        # TODO: setup a lock for the WASM instance
        wasm_instance = wasm_linker.instantiate(wasm_store, wasm_module)
        wasm_memory = wasm_instance.exports(wasm_store)["memory"]

        self.wasm_memory = wasm_memory
        self.wasm_instance = wasm_instance
        self.wasm_store = wasm_store
        self.wasm_linker = wasm_linker
        self.wasm_module = wasm_module
        self.wasm_engine = wasm_engine

        # Bind exported internal AssemblyScript functions
        self.__new = wasm_instance.exports(wasm_store)["__new"]
        self.__pin = wasm_instance.exports(wasm_store)["__pin"]
        self.__unpin = wasm_instance.exports(wasm_store)["__unpin"]

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

        # Extract variable type enum values from WASM
        self.variable_type_map = {
            variable_type_key: wasm_instance.exports(wasm_store)[
                f"VariableType.{variable_type_key}"
            ].value(wasm_store)
            for variable_type_key in [
                "Boolean",
                "String",
                "Number",
                "JSON",
            ]
        }

        # TODO: preallocate header

        # Set and pin the SDK key so it can be reused
        self.sdk_key = sdk_key
        self.sdk_key_addr = self._new_assembly_script_string(sdk_key)
        self.__pin(self.wasm_store, self.sdk_key_addr)

    def _get_export(self, export_name):
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
            pointer = self.__new(self.wasm_store, len(encoded) * 2, object_id_string)
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
        string_length = int.from_bytes(data[pointer - 4: pointer], byteorder="little")
        raw_data = data[pointer: pointer + string_length]

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
        object_id_uint8_array = 9
        object_id_byte_array = 1
        data_length = len(param)
        try:
            # Allocate memory for header.
            header_pointer = self.__new(self.wasm_store, 12, object_id_uint8_array)

            # An external object that is not referenced from within WebAssembly
            # must be pinned whenever an allocation might happen in between
            # allocating it and passing it to WebAssembly.
            pinned_addr = self.__pin(self.wasm_store, header_pointer)
        except Exception as err:
            raise WASMError(f"Error allocating byte array in WASM: {err}")

        try:
            # Allocate memory for buffer.
            buffer_pointer = self.__new(
                self.wasm_store, data_length, object_id_byte_array
            )

            # Get a direct reference to the WASM memory
            data = self.wasm_memory.data_ptr(self.wasm_store)

            # Write the buffer pointer value into the first 4 bytes of the header, little endian.
            for i, b in enumerate(buffer_pointer.to_bytes(4, byteorder="little")):
                data[header_pointer + i] = b
                data[header_pointer + i + 4] = b

            little_endian_buffer_len = data_length.to_bytes(4, byteorder="little")

            # Write the buffer length into bytes 8-12 of the header, little endian.
            for i, b in enumerate(little_endian_buffer_len):
                data[header_pointer + 8 + i] = b

            # Write the byte array data into the WASM buffer.
            for i, b in enumerate(param):
                data[buffer_pointer + i] = b

            return header_pointer
        except Exception as err:
            raise WASMError(f"Error writing byte array to WASM: {err}")
        finally:
            # Unpin the header pointer.
            self.__unpin(self.wasm_store, pinned_addr)

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
            data[pointer + 8: pointer + 12], byteorder="little"
        )
        data_pointer = int.from_bytes(data[pointer: pointer + 4], byteorder="little")

        ret = bytearray(data_length)

        # Copy the data from the WASM buffer into the return value.
        for i in range(data_length):
            ret[i] = data[data_pointer + i]

        return ret

    def get_variable_for_user_protobuf(self, params_buffer) -> str:
        return ""

    def store_config(self, config_json: str) -> None:
        self.wasm_mutex.acquire()
        try:
            data = config_json.encode("utf-8")
            config_addr = self._new_assembly_script_byte_array(data)
            self.setConfigDataUTF8(self.wasm_store, self.sdk_key_addr, config_addr)
        finally:
            self.wasm_mutex.release()

    def set_platform_data(self, platform_json: str) -> None:
        self.wasm_mutex.acquire()
        try:
            data = platform_json.encode("utf-8")
            data_addr = self._new_assembly_script_byte_array(data)
            self.setPlatformDataUTF8(self.wasm_store, data_addr)
        finally:
            self.wasm_mutex.release()
