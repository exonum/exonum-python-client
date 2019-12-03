#!/usr/bin/env python
"""Setup Script for the Exonum Python Light Client."""
import setuptools

INSTALL_REQUIRES = ["protobuf", "pysodium", "requests", "websocket-client-py3"]

PYTHON_REQUIRES = ">=3.4"

with open("README.md", "r") as readme:
    LONG_DESCRIPTION = readme.read()

setuptools.setup(
    name="exonum-python-client",
    version="0.4.0.dev4",
    author="The Exonum team",
    author_email="contact@exonum.com",
    description="Exonum Python Light Client",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/exonum/exonum-python-client",
    packages=[
        "exonum_client",
        "exonum_client.proofs",
        "exonum_client.proofs.map_proof",
        "exonum_client.proofs.list_proof",
    ],
    install_requires=INSTALL_REQUIRES,
    python_requires=PYTHON_REQUIRES,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Security :: Cryptography",
    ],
)
