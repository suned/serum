#!/usr/bin/env bash

python setup.py sdist
python setup.py bdist_wheel
twine upload -u $PYPI_USER -p $PYPI_PASSWORD  dist/*