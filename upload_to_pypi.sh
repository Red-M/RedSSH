#!/bin/bash
mkdir ./tmp
cp -r ./* ./tmp/
cd ./tmp
\rm -rf ./redssh.egg-info ./tmp ./dist
python3 -m pip install --user --upgrade setuptools wheel
python3 -m pip install --user --upgrade twine
python3 setup.py sdist bdist_wheel
twine upload dist/*
cd ../
\rm -rf ./tmp
