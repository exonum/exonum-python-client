#!/usr/bin/env python

from distutils.core import setup

setup(name='exonum',
      description='Python Exonum Client',
      url='https://github.com/exonum/python-client/',
      py_modules=['exonum'],
      install_requires=[
          'nanotime',
          'pysodium'
      ],
      )
