#!/usr/bin/env python
"""Setup Script for the Exonum Python Light Client."""
from distutils.core import setup

INSTALL_REQUIRES = ["protobuf", "google", "pysodium", "requests", "websocket-client-py3"]

PYTHON_REQUIRES = ">=3.4"

setup(
    name="exonum",
    version="0.3",
    description="Exonum Python Light Client",
    url="https://github.com/exonum/python-client/",
    packages=["exonum"],
    install_requires=INSTALL_REQUIRES,
    python_requires=PYTHON_REQUIRES,
)
