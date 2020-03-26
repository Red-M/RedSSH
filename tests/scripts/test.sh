#!/bin/bash
PATH=$PATH:~/.local/bin
CI_SYSTEM=${1}
PYTHON_VERSION=${2}

if [ ! -z $CI_SYSTEM ] && [ ${CI_SYSTEM} != "LOCAL" ]; then
    git checkout origin/master
    eval "$(ssh-agent \-s)"
    chmod 600 ./tests/ssh_host_key
    ssh-add ./tests/ssh_host_key
fi


if [ -n $CI_SYSTEM ] && [ ${CI_SYSTEM} == "GITLAB" ]; then
    git branch master
    chmod 700 /builds /builds/Red_M
fi

if [ ! -z $CI_SYSTEM ] && [ ${CI_SYSTEM} == "TRAVIS" ]; then
    pip${PYTHON_VERSION} install --upgrade pytest coveralls pytest-cov pytest-xdist paramiko > /dev/null
    py.test --cov redssh
else
    pip${PYTHON_VERSION} install --upgrade --user pytest coveralls pytest-cov pytest-xdist paramiko > /dev/null
    py.test --cov redssh --cov-config .coveragerc
fi


coverage html
if [ ! -z $CI_SYSTEM ]; then
    coveralls || true
fi
