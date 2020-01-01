#!/bin/bash
CI_SYSTEM=${1}
PYTHON_MAJOR_VERSION=${2}
PYTHON_MINOR_VERSION=${3}

pip${PYTHON_VERSION} install -e ./[tests]
pip${PYTHON_VERSION} install -e ./[docs]

mkdir ./build
cd ./build
git clone https://github.com/Red-M/ssh2-python.git || true
cd ./ssh2-python
pip${PYTHON_VERSION} uninstall -y ssh2-python
pip${PYTHON_VERSION} install -e ./
cd ../../
