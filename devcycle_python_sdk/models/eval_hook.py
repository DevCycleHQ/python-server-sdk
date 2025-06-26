from typing import Callable, Optional

from devcycle_python_sdk.models.eval_hook_context import HookContext
from devcycle_python_sdk.models.variable import Variable


class EvalHook:
    def __init__(
        self,
        before: Callable[[HookContext], Optional[HookContext]],
        after: Callable[[HookContext, Variable], None],
        on_finally: Callable[[HookContext, Optional[Variable]], None],
        error: Callable[[HookContext, Exception], None],
    ):
        self.before = before
        self.after = after
        self.on_finally = on_finally
        self.error = error
