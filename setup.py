#!/usr/bin/env python
from distutils.core import setup

install_requires = ["protobuf", "google", "pysodium", "requests", "websocket-client-py3"]

python_requires = ">=3.4"

setup(
    name="exonum",
    version="0.2",
    description="Exonum Python Light Client",
    url="https://github.com/exonum/python-client/",
    packages=["exonum"],
    install_requires=install_requires,
    python_requires=python_requires,
)
