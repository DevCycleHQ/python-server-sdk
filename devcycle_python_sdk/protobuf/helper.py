import json
import logging
import math

from typing import Any, Optional

from devcycle_python_sdk.models.variable import TypeEnum, Variable
from devcycle_python_sdk.models.user import User

import devcycle_python_sdk.protobuf.variableForUserParams_pb2 as pb2

logger = logging.getLogger(__name__)


def create_nullable_double(val: Optional[float]) -> pb2.NullableDouble:  # type: ignore
    if val and not math.isnan(val):
        return pb2.NullableDouble(value=val, isNull=False)
    else:
        return pb2.NullableDouble(isNull=True)


def create_nullable_string(val: Optional[str]) -> pb2.NullableString:  # type: ignore
    if val is None:
        return pb2.NullableString(isNull=True)
    else:
        return pb2.NullableString(value=val, isNull=False)


def create_nullable_custom_data(val: Optional[dict]) -> pb2.NullableCustomData:  # type: ignore
    if val:
        values = dict()
        for key, value in val.items():
            if value is None:
                values[key] = pb2.CustomDataValue(type=pb2.CustomDataType.Null)
            elif isinstance(value, bool):
                values[key] = pb2.CustomDataValue(type=pb2.CustomDataType.Bool, boolValue=value)
            elif isinstance(value, str):
                values[key] = pb2.CustomDataValue(type=pb2.CustomDataType.Str, stringValue=value)
            elif isinstance(value, (int, float)):
                values[key] = pb2.CustomDataValue(type=pb2.CustomDataType.Num, doubleValue=value)
            else:
                logger.warning(
                    "Custom Data contains data type that can't be written, will be ignored. Key: %s, Type: %s", key,
                    str(type(value)))

        return pb2.NullableCustomData(value=values, isNull=False)
    else:
        return pb2.NullableCustomData(isNull=True)


def convert_type_enum_to_variable_type(var_type: TypeEnum) -> pb2.VariableType_PB:  # type: ignore
    match var_type:
        case TypeEnum.BOOLEAN:
            return pb2.VariableType_PB.Boolean
        case TypeEnum.STRING:
            return pb2.VariableType_PB.String
        case TypeEnum.NUMBER:
            return pb2.VariableType_PB.Number
        case TypeEnum.JSON:
            return pb2.VariableType_PB.JSON
        case _:
            raise ValueError("Unknown type: " + var_type)


def create_dvcuser_pb(user: User) -> pb2.DVCUser_PB:
    app_build = float('nan')
    if user.appBuild:
        try:
            app_build = float(user.appBuild)
        except ValueError:
            pass

    return pb2.DVCUser_PB(
        user_id=user.user_id,
        email=create_nullable_string(user.email),
        name=create_nullable_string(user.name),
        language=create_nullable_string(user.language),
        country=create_nullable_string(user.country),
        appVersion=create_nullable_string(user.appVersion),
        appBuild=create_nullable_double(app_build),
        customData=create_nullable_custom_data(user.customData),
        privateCustomData=create_nullable_custom_data(user.privateCustomData)
    )


def create_variable(sdk_variable: pb2.SDKVariable_PB, default_value: Any) -> Variable:
    match sdk_variable.type:
        case pb2.VariableType_PB.Boolean:
            return Variable(
                _id=sdk_variable._id,
                value=sdk_variable.boolValue,
                key=sdk_variable.key,
                type=TypeEnum.BOOLEAN,
                isDefaulted=False,
                defaultValue=default_value,
            )

        case pb2.VariableType_PB.String:
            return Variable(
                _id=sdk_variable._id,
                value=sdk_variable.stringValue,
                key=sdk_variable.key,
                type=TypeEnum.STRING,
                isDefaulted=False,
                defaultValue=default_value,
            )

        case pb2.VariableType_PB.Number:
            return Variable(
                _id=sdk_variable._id,
                value=sdk_variable.doubleValue,
                key=sdk_variable.key,
                type=TypeEnum.NUMBER,
                isDefaulted=False,
                defaultValue=default_value,
            )

        case pb2.VariableType_PB.JSON:
            json_data = json.loads(sdk_variable.stringValue)

            return Variable(
                _id=sdk_variable._id,
                value=json_data,
                key=sdk_variable.key,
                type=TypeEnum.JSON,
                isDefaulted=False,
                defaultValue=default_value,
            )

        case _:
            raise ValueError("Unknown type: " + sdk_variable.type)
