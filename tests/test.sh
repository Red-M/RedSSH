#!/bin/bash
PATH=$PATH:~/.local/bin

pip3 install --user coveralls pytest-cov pytest-xdist paramiko > /dev/null
py.test --cov redssh --cov-config .coveragerc
coverage html
# coveralls
