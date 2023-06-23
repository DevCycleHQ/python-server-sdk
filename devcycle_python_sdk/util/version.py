import os


def sdk_version() -> str:
    """
    Returns the current version of this SDK as a semantic version string
    """
    with open(os.path.dirname(__file__) + "/../VERSION.txt", "r") as version_file:
        return version_file.read().strip()
