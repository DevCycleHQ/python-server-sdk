# coding: utf-8

from setuptools import setup, find_packages
import os

NAME = "devcycle-python-server-sdk"
version_file = open(os.path.join("devcycle_python_sdk", "VERSION.txt"))
VERSION = version_file.read().strip()

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [line.strip() for line in open("requirements.txt").readlines()]

setup(
    name=NAME,
    version=VERSION,
    description="DevCycle Python SDK",
    author_email="",
    url="https://github.com/devcycleHQ/python-server-sdk",
    keywords=["DevCycle"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={
        "": ["VERSION.txt"],
        "devcycle_python_sdk": ["py.typed", "bucketing-lib.release.wasm"],
    },
    include_package_data=True,
    long_description="""\
    The DevCycle Python SDK used for feature management.
    """,
)
