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
    export LC_ALL=C.UTF-8
    export LANG=C.UTF-8
fi

if [ ! -z $CI_SYSTEM ] && [ ${CI_SYSTEM} == "TRAVIS" ]; then
    pip${PYTHON_VERSION} install --upgrade pytest coveralls pytest-cov pytest-xdist paramiko > /dev/null
    py.test --cov redssh
else
    pip${PYTHON_VERSION} install --upgrade --user pytest coveralls pytest-cov pytest-xdist paramiko > /dev/null
    py.test --cov redssh --cov-config .coveragerc
fi


echo "*********** Coveralls ***********"
coverage html
if [ ! -z $CI_SYSTEM ]; then
    coveralls || true
fi

CODE_VALIDATION_PY_FILES="$(find ./ -type f | grep '\.py$' | grep -v 'tests/')" # Ignore tests for now.
BANDIT_REPORT=$(tempfile)
PYLINT_REPORT=$(tempfile)
SAFETY_REPORT=$(tempfile)
echo "*********** Bandit ***********"
bandit -c ./.bandit.yml -r ${CODE_VALIDATION_PY_FILES} 2>&1 > "${BANDIT_REPORT}"
cat "${BANDIT_REPORT}"

echo "*********** Pylint ***********"
pylint ${CODE_VALIDATION_PY_FILES} 2>&1 > "${PYLINT_REPORT}"
cat "${PYLINT_REPORT}"

echo "*********** Safety ***********"
safety check 2>&1 > "${SAFETY_REPORT}"
cat "${SAFETY_REPORT}"
