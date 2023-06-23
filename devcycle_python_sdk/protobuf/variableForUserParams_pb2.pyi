from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

Bool: CustomDataType
Boolean: VariableType_PB
DESCRIPTOR: _descriptor.FileDescriptor
JSON: VariableType_PB
Null: CustomDataType
Num: CustomDataType
Number: VariableType_PB
Str: CustomDataType
String: VariableType_PB

class CustomDataValue(_message.Message):
    __slots__ = ["boolValue", "doubleValue", "stringValue", "type"]
    BOOLVALUE_FIELD_NUMBER: _ClassVar[int]
    DOUBLEVALUE_FIELD_NUMBER: _ClassVar[int]
    STRINGVALUE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    boolValue: bool
    doubleValue: float
    stringValue: str
    type: CustomDataType
    def __init__(self, type: _Optional[_Union[CustomDataType, str]] = ..., boolValue: bool = ..., doubleValue: _Optional[float] = ..., stringValue: _Optional[str] = ...) -> None: ...

class DVCUser_PB(_message.Message):
    __slots__ = ["appBuild", "appVersion", "country", "customData", "deviceModel", "email", "language", "name", "privateCustomData", "user_id"]
    APPBUILD_FIELD_NUMBER: _ClassVar[int]
    APPVERSION_FIELD_NUMBER: _ClassVar[int]
    COUNTRY_FIELD_NUMBER: _ClassVar[int]
    CUSTOMDATA_FIELD_NUMBER: _ClassVar[int]
    DEVICEMODEL_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PRIVATECUSTOMDATA_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    appBuild: NullableDouble
    appVersion: NullableString
    country: NullableString
    customData: NullableCustomData
    deviceModel: NullableString
    email: NullableString
    language: NullableString
    name: NullableString
    privateCustomData: NullableCustomData
    user_id: str
    def __init__(self, user_id: _Optional[str] = ..., email: _Optional[_Union[NullableString, _Mapping]] = ..., name: _Optional[_Union[NullableString, _Mapping]] = ..., language: _Optional[_Union[NullableString, _Mapping]] = ..., country: _Optional[_Union[NullableString, _Mapping]] = ..., appBuild: _Optional[_Union[NullableDouble, _Mapping]] = ..., appVersion: _Optional[_Union[NullableString, _Mapping]] = ..., deviceModel: _Optional[_Union[NullableString, _Mapping]] = ..., customData: _Optional[_Union[NullableCustomData, _Mapping]] = ..., privateCustomData: _Optional[_Union[NullableCustomData, _Mapping]] = ...) -> None: ...

class NullableCustomData(_message.Message):
    __slots__ = ["isNull", "value"]
    class ValueEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: CustomDataValue
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[CustomDataValue, _Mapping]] = ...) -> None: ...
    ISNULL_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    isNull: bool
    value: _containers.MessageMap[str, CustomDataValue]
    def __init__(self, value: _Optional[_Mapping[str, CustomDataValue]] = ..., isNull: bool = ...) -> None: ...

class NullableDouble(_message.Message):
    __slots__ = ["isNull", "value"]
    ISNULL_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    isNull: bool
    value: float
    def __init__(self, value: _Optional[float] = ..., isNull: bool = ...) -> None: ...

class NullableString(_message.Message):
    __slots__ = ["isNull", "value"]
    ISNULL_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    isNull: bool
    value: str
    def __init__(self, value: _Optional[str] = ..., isNull: bool = ...) -> None: ...

class SDKVariable_PB(_message.Message):
    __slots__ = ["_id", "boolValue", "doubleValue", "evalReason", "key", "stringValue", "type"]
    BOOLVALUE_FIELD_NUMBER: _ClassVar[int]
    DOUBLEVALUE_FIELD_NUMBER: _ClassVar[int]
    EVALREASON_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    STRINGVALUE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    _ID_FIELD_NUMBER: _ClassVar[int]
    _id: str
    boolValue: bool
    doubleValue: float
    evalReason: NullableString
    key: str
    stringValue: str
    type: VariableType_PB
    def __init__(self, _id: _Optional[str] = ..., type: _Optional[_Union[VariableType_PB, str]] = ..., key: _Optional[str] = ..., boolValue: bool = ..., doubleValue: _Optional[float] = ..., stringValue: _Optional[str] = ..., evalReason: _Optional[_Union[NullableString, _Mapping]] = ...) -> None: ...

class VariableForUserParams_PB(_message.Message):
    __slots__ = ["sdkKey", "shouldTrackEvent", "user", "variableKey", "variableType"]
    SDKKEY_FIELD_NUMBER: _ClassVar[int]
    SHOULDTRACKEVENT_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    VARIABLEKEY_FIELD_NUMBER: _ClassVar[int]
    VARIABLETYPE_FIELD_NUMBER: _ClassVar[int]
    sdkKey: str
    shouldTrackEvent: bool
    user: DVCUser_PB
    variableKey: str
    variableType: VariableType_PB
    def __init__(self, sdkKey: _Optional[str] = ..., variableKey: _Optional[str] = ..., variableType: _Optional[_Union[VariableType_PB, str]] = ..., user: _Optional[_Union[DVCUser_PB, _Mapping]] = ..., shouldTrackEvent: bool = ...) -> None: ...

class VariableType_PB(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class CustomDataType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
