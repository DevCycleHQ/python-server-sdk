import json
import logging
import math

from typing import Any, Optional

from devcycle_python_sdk.models.variable import TypeEnum, Variable
from devcycle_python_sdk.models.user import DevCycleUser

import devcycle_python_sdk.protobuf.variableForUserParams_pb2 as pb2

logger = logging.getLogger(__name__)


def create_nullable_double(val: Optional[float]) -> pb2.NullableDouble:  # type: ignore
    if val and not math.isnan(val):
        return pb2.NullableDouble(value=val, isNull=False)  # type: ignore
    else:
        return pb2.NullableDouble(isNull=True)  # type: ignore


def create_nullable_string(val: Optional[str]) -> pb2.NullableString:  # type: ignore
    if val is None:
        return pb2.NullableString(isNull=True)  # type: ignore
    else:
        return pb2.NullableString(value=val, isNull=False)  # type: ignore


def create_nullable_custom_data(val: Optional[dict]) -> pb2.NullableCustomData:  # type: ignore
    if val:
        values = dict()
        for key, value in val.items():
            if value is None:
                values[key] = pb2.CustomDataValue(type=pb2.CustomDataType.Null)  # type: ignore
            elif isinstance(value, bool):
                values[key] = pb2.CustomDataValue(type=pb2.CustomDataType.Bool, boolValue=value)  # type: ignore
            elif isinstance(value, str):
                values[key] = pb2.CustomDataValue(type=pb2.CustomDataType.Str, stringValue=value)  # type: ignore
            elif isinstance(value, (int, float)):
                values[key] = pb2.CustomDataValue(type=pb2.CustomDataType.Num, doubleValue=value)  # type: ignore
            else:
                logger.warning(
                    f"Custom Data contains data type that can't be written, will be ignored. Key: {key}, Type: {str(type(value))}"
                )

        return pb2.NullableCustomData(value=values, isNull=False)  # type: ignore
    else:
        return pb2.NullableCustomData(isNull=True)  # type: ignore


def convert_type_enum_to_variable_type(var_type: str) -> pb2.VariableType_PB:
    if var_type == TypeEnum.BOOLEAN:
        return pb2.VariableType_PB.Boolean
    elif var_type == TypeEnum.STRING:
        return pb2.VariableType_PB.String
    elif var_type == TypeEnum.NUMBER:
        return pb2.VariableType_PB.Number
    elif var_type == TypeEnum.JSON:
        return pb2.VariableType_PB.JSON
    else:
        raise ValueError("Unknown type: " + str(var_type))


def create_dvcuser_pb(user: DevCycleUser) -> pb2.DVCUser_PB:  # type: ignore
    app_build = float("nan")
    if user.appBuild:
        try:
            app_build = float(user.appBuild)
        except ValueError:
            pass

    return pb2.DVCUser_PB(  # type: ignore
        user_id=user.user_id,
        email=create_nullable_string(user.email),
        name=create_nullable_string(user.name),
        language=create_nullable_string(user.language),
        country=create_nullable_string(user.country),
        appVersion=create_nullable_string(user.appVersion),
        appBuild=create_nullable_double(app_build),
        customData=create_nullable_custom_data(user.customData),
        privateCustomData=create_nullable_custom_data(user.privateCustomData),
    )


def create_variable(sdk_variable: pb2.SDKVariable_PB, default_value: Any) -> Variable:  # type: ignore
    if sdk_variable.type == pb2.VariableType_PB.Boolean:  # type: ignore
        return Variable(
            _id=None,
            value=sdk_variable.boolValue,
            key=sdk_variable.key,
            type=TypeEnum.BOOLEAN,
            isDefaulted=False,
            defaultValue=default_value,
        )

    elif sdk_variable.type == pb2.VariableType_PB.String:  # type: ignore
        return Variable(
            _id=None,
            value=sdk_variable.stringValue,
            key=sdk_variable.key,
            type=TypeEnum.STRING,
            isDefaulted=False,
            defaultValue=default_value,
        )

    elif sdk_variable.type == pb2.VariableType_PB.Number:  # type: ignore
        return Variable(
            _id=None,
            value=sdk_variable.doubleValue,
            key=sdk_variable.key,
            type=TypeEnum.NUMBER,
            isDefaulted=False,
            defaultValue=default_value,
        )

    elif sdk_variable.type == pb2.VariableType_PB.JSON:  # type: ignore
        json_data = json.loads(sdk_variable.stringValue)

        return Variable(
            _id=None,
            value=json_data,
            key=sdk_variable.key,
            type=TypeEnum.JSON,
            isDefaulted=False,
            defaultValue=default_value,
        )

    else:
        raise ValueError("Unknown type: " + sdk_variable.type)
