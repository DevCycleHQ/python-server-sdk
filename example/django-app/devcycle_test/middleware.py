from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from devcycle_python_sdk import (
    DevCycleCloudClient,
    DevCycleCloudOptions,
    DevCycleLocalClient,
    DevCycleLocalOptions,
)


def devcycle_cloud_middleware(get_response):
    """
    This middleware adds the DevCycle client to the request object passed to
    all views as `request.devcycle`.
    """
    try:
        sdk_key = settings.DEVCYCLE_SERVER_SDK_KEY
    except AttributeError:
        raise ImproperlyConfigured("Please set DEVCYCLE_SERVER_SDK_KEY in settings.py")

    # Initialize the SDK singleton once here - it will be captured in the closure below
    devcycle_client = DevCycleCloudClient(sdk_key, DevCycleCloudOptions())

    def middleware(request):
        request.devcycle = devcycle_client
        return get_response(request)

    return middleware


def devcycle_local_middleware(get_response):
    """
    This middleware adds the DevCycle client to the request object passed to
    all views as `request.devcycle`.
    """
    try:
        sdk_key = settings.DEVCYCLE_SERVER_SDK_KEY
    except AttributeError:
        raise ImproperlyConfigured("Please set DEVCYCLE_SERVER_SDK_KEY in settings.py")

    # Initialize the SDK singleton once here - it will be captured in the closure below
    devcycle_client = DevCycleLocalClient(sdk_key, DevCycleLocalOptions())

    def middleware(request):
        request.devcycle = devcycle_client
        return get_response(request)

    return middleware
