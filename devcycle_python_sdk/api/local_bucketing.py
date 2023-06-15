import logging
from pathlib import Path
import random
import time

import wasmtime
from wasmtime import (
    Store,
    Module,
    Instance,  # noqa
    Linker,
    Func,
    FuncType,
    Config,  # noqa
    Engine,
    ValType,
)

logger = logging.getLogger(__name__)

wasm_path = Path(__file__).parent.parent / "bucketing-lib.debug.wasm"


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
            wasm_path,
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

        def __abort_func(caller, message_ptr, filename_ptr, line, column):
            message: str = self.read_wasm_string(message_ptr)
            filename: str = self.read_wasm_string(filename_ptr)
            raise RuntimeError(f"Exception in {filename}:{line}:{column}  -- {message}")

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

        def __console_log_func(message_ptr):
            message: str = self.read_wasm_string(message_ptr)
            logger.warning(f"WASM console: {message}")

        wasm_linker.define_func(
            "env", "console.log", FuncType([ValType.i32()], []), __console_log_func
        )

        # TODO: What does this do?
        wasm_linker.define_module(wasm_store, "", wasm_module)

        wasm_instance = wasm_linker.instantiate(wasm_store, wasm_module)
        wasm_memory = wasm_instance.exports(wasm_store)["memory"]

        # Bind exported internal AssemblyScript functions
        self.__new: Func = wasm_instance.exports(wasm_store)["__new"]
        self.__pin: Func = wasm_instance.exports(wasm_store)["__pin"]
        self.__unpin: Func = wasm_instance.exports(wasm_store)["__unpin"]

        # TODO: Is collect used?
        self.__collect: Func = wasm_instance.exports(wasm_store)["__collect"]

        self.initEventQueue = wasm_instance.exports(wasm_store)["initEventQueue"]
        self.flushEventQueue = wasm_instance.exports(wasm_store)["flushEventQueue"]
        self.eventQueueSize = wasm_instance.exports(wasm_store)["eventQueueSize"]
        self.onPayloadSuccess = wasm_instance.exports(wasm_store)["onPayloadSuccess"]
        self.onPayloadFailure = wasm_instance.exports(wasm_store)["onPayloadFailure"]
        self.queueEvent = wasm_instance.exports(wasm_store)["queueEvent"]
        self.queueAggregateEvent = wasm_instance.exports(wasm_store)[
            "queueAggregateEvent"
        ]
        self.setConfigDataUTF8 = wasm_instance.exports(wasm_store)["setConfigDataUTF8"]
        self.setPlatformDataUTF8 = wasm_instance.exports(wasm_store)[
            "setPlatformDataUTF8"
        ]
        self.setClientCustomDataUTF8 = wasm_instance.exports(wasm_store)[
            "setClientCustomDataUTF8"
        ]
        self.generateBucketedConfigForUserUTF8 = wasm_instance.exports(wasm_store)[
            "generateBucketedConfigForUserUTF8"
        ]

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

        self.wasm_memory = wasm_memory
        self.wasm_instance = wasm_instance
        self.wasm_store = wasm_store
        self.wasm_linker = wasm_linker
        self.wasm_module = wasm_module
        self.wasm_engine = wasm_engine

    def read_wasm_string(self, string_ptr):
        return "Not Implemented"


if __name__ == "__main__":
    lb = LocalBucketing()
