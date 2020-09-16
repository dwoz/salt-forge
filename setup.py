#!/usr/bin/env python

from distutils.core import setup

setup(
  name='SaltForge',
  version='1.0',
  description='Local salt development environments',
  author='Daniel A. Wozniak',
  author_email='dan@woz.io',
  url='https://woz.io',
  scripts=['salt-forge.py'],
  py_modules=['salt_forge_bootstrap'],
)
