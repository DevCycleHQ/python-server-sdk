from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class VariableType_PB(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    Boolean: _ClassVar[VariableType_PB]
    Number: _ClassVar[VariableType_PB]
    String: _ClassVar[VariableType_PB]
    JSON: _ClassVar[VariableType_PB]

class CustomDataType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    Bool: _ClassVar[CustomDataType]
    Num: _ClassVar[CustomDataType]
    Str: _ClassVar[CustomDataType]
    Null: _ClassVar[CustomDataType]
Boolean: VariableType_PB
Number: VariableType_PB
String: VariableType_PB
JSON: VariableType_PB
Bool: CustomDataType
Num: CustomDataType
Str: CustomDataType
Null: CustomDataType

class NullableString(_message.Message):
    __slots__ = ("value", "isNull")
    VALUE_FIELD_NUMBER: _ClassVar[int]
    ISNULL_FIELD_NUMBER: _ClassVar[int]
    value: str
    isNull: bool
    def __init__(self, value: _Optional[str] = ..., isNull: bool = ...) -> None: ...

class NullableDouble(_message.Message):
    __slots__ = ("value", "isNull")
    VALUE_FIELD_NUMBER: _ClassVar[int]
    ISNULL_FIELD_NUMBER: _ClassVar[int]
    value: float
    isNull: bool
    def __init__(self, value: _Optional[float] = ..., isNull: bool = ...) -> None: ...

class CustomDataValue(_message.Message):
    __slots__ = ("type", "boolValue", "doubleValue", "stringValue")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    BOOLVALUE_FIELD_NUMBER: _ClassVar[int]
    DOUBLEVALUE_FIELD_NUMBER: _ClassVar[int]
    STRINGVALUE_FIELD_NUMBER: _ClassVar[int]
    type: CustomDataType
    boolValue: bool
    doubleValue: float
    stringValue: str
    def __init__(self, type: _Optional[_Union[CustomDataType, str]] = ..., boolValue: bool = ..., doubleValue: _Optional[float] = ..., stringValue: _Optional[str] = ...) -> None: ...

class NullableCustomData(_message.Message):
    __slots__ = ("value", "isNull")
    class ValueEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: CustomDataValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[CustomDataValue, _Mapping]] = ...) -> None: ...
    VALUE_FIELD_NUMBER: _ClassVar[int]
    ISNULL_FIELD_NUMBER: _ClassVar[int]
    value: _containers.MessageMap[str, CustomDataValue]
    isNull: bool
    def __init__(self, value: _Optional[_Mapping[str, CustomDataValue]] = ..., isNull: bool = ...) -> None: ...

class VariableForUserParams_PB(_message.Message):
    __slots__ = ("sdkKey", "variableKey", "variableType", "user", "shouldTrackEvent")
    SDKKEY_FIELD_NUMBER: _ClassVar[int]
    VARIABLEKEY_FIELD_NUMBER: _ClassVar[int]
    VARIABLETYPE_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    SHOULDTRACKEVENT_FIELD_NUMBER: _ClassVar[int]
    sdkKey: str
    variableKey: str
    variableType: VariableType_PB
    user: DVCUser_PB
    shouldTrackEvent: bool
    def __init__(self, sdkKey: _Optional[str] = ..., variableKey: _Optional[str] = ..., variableType: _Optional[_Union[VariableType_PB, str]] = ..., user: _Optional[_Union[DVCUser_PB, _Mapping]] = ..., shouldTrackEvent: bool = ...) -> None: ...

class DVCUser_PB(_message.Message):
    __slots__ = ("user_id", "email", "name", "language", "country", "appBuild", "appVersion", "deviceModel", "customData", "privateCustomData")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    APPBUILD_FIELD_NUMBER: _ClassVar[int]
    APPVERSION_FIELD_NUMBER: _ClassVar[int]
    DEVICEMODEL_FIELD_NUMBER: _ClassVar[int]
    CUSTOMDATA_FIELD_NUMBER: _ClassVar[int]
    PRIVATECUSTOMDATA_FIELD_NUMBER: _ClassVar[int]
    user_id: str
    email: NullableString
    name: NullableString
    language: NullableString
    country: NullableString
    appBuild: NullableDouble
    appVersion: NullableString
    deviceModel: NullableString
    customData: NullableCustomData
    privateCustomData: NullableCustomData
    def __init__(self, user_id: _Optional[str] = ..., email: _Optional[_Union[NullableString, _Mapping]] = ..., name: _Optional[_Union[NullableString, _Mapping]] = ..., language: _Optional[_Union[NullableString, _Mapping]] = ..., country: _Optional[_Union[NullableString, _Mapping]] = ..., appBuild: _Optional[_Union[NullableDouble, _Mapping]] = ..., appVersion: _Optional[_Union[NullableString, _Mapping]] = ..., deviceModel: _Optional[_Union[NullableString, _Mapping]] = ..., customData: _Optional[_Union[NullableCustomData, _Mapping]] = ..., privateCustomData: _Optional[_Union[NullableCustomData, _Mapping]] = ...) -> None: ...

class SDKVariable_PB(_message.Message):
    __slots__ = ("_id", "type", "key", "boolValue", "doubleValue", "stringValue", "evalReason", "_feature", "eval")
    _ID_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    BOOLVALUE_FIELD_NUMBER: _ClassVar[int]
    DOUBLEVALUE_FIELD_NUMBER: _ClassVar[int]
    STRINGVALUE_FIELD_NUMBER: _ClassVar[int]
    EVALREASON_FIELD_NUMBER: _ClassVar[int]
    _FEATURE_FIELD_NUMBER: _ClassVar[int]
    EVAL_FIELD_NUMBER: _ClassVar[int]
    _id: str
    type: VariableType_PB
    key: str
    boolValue: bool
    doubleValue: float
    stringValue: str
    evalReason: NullableString
    _feature: NullableString
    eval: EvalReason_PB
    def __init__(self, _id: _Optional[str] = ..., type: _Optional[_Union[VariableType_PB, str]] = ..., key: _Optional[str] = ..., boolValue: bool = ..., doubleValue: _Optional[float] = ..., stringValue: _Optional[str] = ..., evalReason: _Optional[_Union[NullableString, _Mapping]] = ..., _feature: _Optional[_Union[NullableString, _Mapping]] = ..., eval: _Optional[_Union[EvalReason_PB, _Mapping]] = ...) -> None: ...

class EvalReason_PB(_message.Message):
    __slots__ = ("reason", "details", "target_id")
    REASON_FIELD_NUMBER: _ClassVar[int]
    DETAILS_FIELD_NUMBER: _ClassVar[int]
    TARGET_ID_FIELD_NUMBER: _ClassVar[int]
    reason: str
    details: str
    target_id: str
    def __init__(self, reason: _Optional[str] = ..., details: _Optional[str] = ..., target_id: _Optional[str] = ...) -> None: ...
