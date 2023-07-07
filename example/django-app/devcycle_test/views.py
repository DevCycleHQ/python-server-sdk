from django.http import HttpResponse
import logging

from devcycle_python_sdk.models.user import DevCycleUser

logger = logging.getLogger(__name__)

variable_key = "test-boolean-variable"


def home_page(request):
    # all functions require user data to be an instance of the User class
    user = DevCycleUser(
        user_id="test",
        email="example@example.ca",
        country="CA",
    )
    # Check whether a feature flag is on
    if request.devcycle.variable_value(user, variable_key, False):
        logger.info(f"{variable_key} is on")
        return HttpResponse("Hello, World! Your feature is on!")
    else:
        logger.info(f"{variable_key} is off")
        return HttpResponse("Hello, World! Your feature is off.")
