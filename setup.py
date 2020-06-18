# python setup.py install
# it will create a console script GE_parse

from setuptools import setup, find_packages

# Parse requirements.txt
with open('requirements.txt') as f:
    required = f.read().splitlines()

config = {
  "description": "Using Python Abstract Syntax Trees (ast) to parse DocStrings in the GE codebase",
  "author": "William Shin",
  "url": "https://github.com/Shinnnyshinshin/GE_DataDocs_Parser",
  "author_email": "willshin@gmail.com",
  "version": "0.0.1",
  "install_requires": required,
  "packages": find_packages(exclude=["docs", "tests", "examples"]),
  "name": "DataDocs_Parser",
  'entry_points': {
    'console_scripts': ['GE_parse=GE_DataDocs_Parser.cli:main']
  },
}

setup(**config)
