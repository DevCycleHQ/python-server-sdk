import os


def sdk_version() -> str:
    """
    Returns the current version of this SDK as a semantic version string
    """
    version_file = open(os.path.join('devcycle_python_sdk', 'VERSION.txt'))
    return version_file.read().strip()
