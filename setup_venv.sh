#!/usr/bin/env bash

pip3 install virtualenv

if [ -d  venv3 ]; then
  rm -rf venv3
fi

virtualenv --no-site-packages --python=python3.6 venv3
venv3/bin/pip install -r requirements.txt
venv3/bin/pip install -r requirements-dev.txt
