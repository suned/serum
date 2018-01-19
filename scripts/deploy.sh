#!/usr/bin/env bash

python setup.py sdist
python setup.py bdist_wheel
twine -u $PYPI_USER -p $PYPI_PASSWORD upload dist/*