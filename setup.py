#!/usr/bin/env python
import sys

from distutils.core import setup

install_requires = [
    'nanotime',
    'pysodium',
    'six'
]

python_requires = '>=3.4'

if sys.version_info.major == 2:
    install_requires.append('py2-ipaddress')
    python_requires = '>=2.7'

setup(name='exonum',
      version="0.1dev",
      description='Python Exonum Client',
      url='https://github.com/exonum/python-client/',
      packages=['exonum'],
      install_requires=install_requires,
      python_requires=python_requires)
