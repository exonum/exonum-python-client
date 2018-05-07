#!/usr/bin/env python

from distutils.core import setup

setup(name='exonum',
      description='Python Exonum Client',
      url='https://github.com/exonum/python-client/',
      py_modules=['exonum'],
      package_dir={'exonum': 'exonum'},
      python_requires='>=3.5',
      install_requires=[
          'nanotime',
          'pysodium'
      ],
      )
