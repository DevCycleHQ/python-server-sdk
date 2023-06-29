# ruff: noqa: N815
import platform
import socket
from dataclasses import dataclass
from devcycle_python_sdk.util.version import sdk_version


@dataclass(order=False)
class PlatformData:
    sdkType: str
    sdkVersion: str
    platformVersion: str
    deviceModel: str
    platform: str
    hostname: str

    def to_json(self):
        return {
            key: getattr(self, key)
            for key in self.__dataclass_fields__
            if getattr(self, key) is not None
        }


def default_platform_data() -> PlatformData:
    return PlatformData(
        sdkType="server",
        sdkVersion=sdk_version(),
        platformVersion=platform.python_version(),
        deviceModel=platform.platform(),
        platform="Python",
        hostname=socket.gethostname(),
    )
