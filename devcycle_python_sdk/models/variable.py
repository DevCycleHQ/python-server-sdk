# ruff: noqa: N815
from dataclasses import dataclass
from typing import Optional, Any

from .eval_reason import EvalReason, EvalReasons


class TypeEnum:
    BOOLEAN = "Boolean"
    STRING = "String"
    NUMBER = "Number"
    JSON = "JSON"


def determine_variable_type(value: Any) -> str:
    if isinstance(value, bool):
        return TypeEnum.BOOLEAN
    elif isinstance(value, str):
        return TypeEnum.STRING
    elif isinstance(value, (int, float)):
        return TypeEnum.NUMBER
    elif isinstance(value, dict):
        return TypeEnum.JSON
    else:
        raise TypeError(f"Unsupported type: {type(value)}")


@dataclass(order=False)
class Variable:
    _id: Optional[str]
    key: str
    type: str
    value: Any = None
    isDefaulted: Optional[bool] = False
    defaultValue: Any = None
    evalReason: Optional[str] = None
    eval: Optional[EvalReason] = None

    def to_json(self):
        result = {}
        for key in self.__dataclass_fields__:
            value = getattr(self, key)
            if value is not None:
                if key == "eval" and isinstance(value, EvalReason):
                    result[key] = value.to_json()
                else:
                    result[key] = value
        return result

    @classmethod
    def from_json(cls, data: dict) -> "Variable":
        eval_data = data.get("eval")
        eval_reason = None
        if eval_data:
            eval_reason = EvalReason.from_json(eval_data)

        return cls(
            _id=data["_id"],
            key=data["key"],
            type=data["type"],
            value=data["value"],
            isDefaulted=data.get("isDefaulted", None),
            defaultValue=data.get("defaultValue"),
            evalReason=data.get("evalReason"),
            eval=eval_reason,
        )

    @staticmethod
    def create_default_variable(
        key: str, default_value: Any, default_reason_detail: Optional[str] = None
    ) -> "Variable":
        var_type = determine_variable_type(default_value)
        if default_reason_detail is not None:
            eval_reason = EvalReason(
                reason=EvalReasons.DEFAULT, details=default_reason_detail
            )
        else:
            eval_reason = None
        return Variable(
            _id=None,
            key=key,
            type=var_type,
            value=default_value,
            defaultValue=default_value,
            isDefaulted=True,
            eval=eval_reason,
        )

    def get_flag_meta_data(self) -> dict:
        """
        Returns metadata dictionary for OpenFeature flag resolution.

        Returns:
            dict: Dictionary containing evalReasonDetails and evalReasonTargetId
                  if they exist, empty dict otherwise.
        """
        meta_data = {}
        if self.eval:
            if self.eval.details:
                meta_data["evalReasonDetails"] = self.eval.details
            if self.eval.target_id:
                meta_data["evalReasonTargetId"] = self.eval.target_id
        return meta_data
