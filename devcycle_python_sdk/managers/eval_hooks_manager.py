from typing import List, Optional

from devcycle_python_sdk.models.eval_hook import EvalHook
from devcycle_python_sdk.models.eval_hook_context import HookContext
from devcycle_python_sdk.models.variable import Variable
from devcycle_python_sdk.options import logger


class BeforeHookError(Exception):
    """Exception raised when a before hook fails"""

    def __init__(self, message: str, original_error: Exception):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class AfterHookError(Exception):
    """Exception raised when an after hook fails"""

    def __init__(self, message: str, original_error: Exception):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class EvalHooksManager:
    def __init__(self, hooks: Optional[List[EvalHook]] = None):
        self.hooks: List[EvalHook] = hooks if hooks is not None else []

    def add_hook(self, hook: EvalHook) -> None:
        """Add an evaluation hook to be executed"""
        self.hooks.append(hook)

    def clear_hooks(self) -> None:
        """Clear all evaluation hooks"""
        self.hooks = []

    def run_before(self, context: HookContext) -> Optional[HookContext]:
        """Run before hooks and return modified context if any"""
        modified_context = context
        for hook in self.hooks:
            try:
                result = hook.before(modified_context)
                if result:
                    modified_context = result
            except Exception as e:
                raise BeforeHookError(f"Before hook failed: {e}", e)
        return modified_context

    def run_after(self, context: HookContext, variable: Variable) -> None:
        """Run after hooks with the evaluation result"""
        for hook in self.hooks:
            try:
                hook.after(context, variable)
            except Exception as e:
                raise AfterHookError(f"After hook failed: {e}", e)

    def run_finally(self, context: HookContext, variable: Optional[Variable]) -> None:
        """Run finally hooks after evaluation completes"""
        for hook in self.hooks:
            try:
                hook.on_finally(context, variable)
            except Exception as e:
                logger.error(f"Error running finally hook: {e}")

    def run_error(self, context: HookContext, error: Exception) -> None:
        """Run error hooks when an error occurs"""
        for hook in self.hooks:
            try:
                hook.error(context, error)
            except Exception as e:
                logger.error(f"Error running error hook: {e}")
