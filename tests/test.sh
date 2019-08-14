#!/bin/bash
PATH=$PATH:~/.local/bin

pip3 install --user coveralls pytest-cov paramiko > /dev/null
py.test --cov redssh --cov-config .coveragerc
coverage combine
# coveralls
