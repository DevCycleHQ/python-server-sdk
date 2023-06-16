import logging
from pathlib import Path
import random
import time

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


class LocalBucketing:
    def __init__(self):
        self.random = random.random()

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

        def __abort_func(caller, message_ptr, filename_ptr, line, column) -> None:
            message: bytes = self._read_assembly_script_string(message_ptr)
            filename: bytes = self._read_assembly_script_string(filename_ptr)
            # TODO: make sure throwing an exception here results in a reasonable error message
            raise RuntimeError(
                f"Exception in {filename!r}:{line}:{column}  -- {message!r}"
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
            message: bytes = self._read_assembly_script_string(message_ptr)
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

        # TODO: Is collect used?
        self.__collect = wasm_instance.exports(wasm_store)["__collect"]

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

        # TODO: set SDK key

        # TODO: set platform JSON

    def _get_export(self, export_name):
        return self.wasm_instance.exports(self.wasm_store)[export_name]

    def _new_assembly_script_string(self, param: bytes) -> int:
        """
        Allocate memory for a string in AssemblyScript and write the string
        into memory, then return a pointer to the string.
        Only safe for use with ASCII strings.
        """
        object_id_string = 2
        try:
            # Create pointer to string buffer in WASM memory.
            pointer = self.__new(self.wasm_store, len(param) * 2, object_id_string)
        except Exception as err:
            logger.error(f"__new (_new_assembly_script_string) error: {err}")
            return -1
        addr = pointer
        data = self.wasm_memory.data_ptr(self.wasm_store)

        # Write data into buffer.
        for i, c in enumerate(param):
            data[addr + i * 2] = c

        # TODO: Does this happen? Or do we just get an exception?
        if pointer == 0:
            logger.error("Failed to allocate memory for string")
            raise WASMError("Failed to allocate memory for string")

        return pointer

    def _read_assembly_script_string(self, pointer: int) -> bytes:
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

        return ret

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

            # TODO: Do we actually need to pin the header pointer?
            pinned_addr = self.__pin(self.wasm_store, header_pointer)
        except Exception as err:
            logger.error(f"__new (new_assembly_script_byte_array) error: {err}")
            return -1

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

            little_endian_buffer_len = data_length.to_bytes(4, byteorder="little")

            # Write the buffer length into bytes 8-12 of the header, little endian.
            for i, b in enumerate(little_endian_buffer_len):
                data[header_pointer + 8 + i] = b

            # Write the byte array data into the WASM buffer.
            for i, b in enumerate(param):
                data[buffer_pointer + i] = b

            return header_pointer
        except Exception as err:
            logger.error(f"__new (new_assembly_script_byte_array) error: {err}")
            return -1
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
            data[pointer + 8 : pointer + 12], byteorder="little"
        )
        data_pointer = int.from_bytes(data[pointer : pointer + 4], byteorder="little")

        ret = bytearray(data_length)

        # Copy the data from the WASM buffer into the return value.
        for i in range(data_length):
            ret[i] = data[data_pointer + i]

        return ret


if __name__ == "__main__":
    lb = LocalBucketing()
    logger.warning([export.name for export in lb.wasm_module.exports])
