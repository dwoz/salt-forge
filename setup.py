#!/usr/bin/env python
import os.path
from distutils.core import setup

data_path = os.path.join(os.path.expanduser("~"), '.local', 'salt-forge')

setup(
  name='SaltForge',
  version='1.0',
  description='Local salt development environments',
  author='Daniel A. Wozniak',
  author_email='dan@woz.io',
  url='https://woz.io',
  scripts=['salt-forge.py'],
  py_modules=['salt_forge_bootstrap'],
  data_files=[
    (data_path, ['config.yml'])
  ],
)
