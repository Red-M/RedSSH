# RedSSH
[![Documentation Status](https://readthedocs.org/projects/redssh/badge/?version=latest)](https://redssh.readthedocs.io/en/latest/?badge=latest)

Connect to SSH servers in python easily and with C speed!
Interacting with SSH shouldn't be hard, slow or limited to certain SSH severs.
Based on ssh2-python (which provides libssh2 bindings for python) and made into an easy to use SSH library with the focus being ease of use and speed.
SSH should be as easy as a pre-wrapped TLS TCP socket, it should work well, be fast in execution and be simple to interact with.


# Installing

RedSSH can be installed via pip with `pip install redssh` or the latest commit, which may not be the most stable, from git with `pip install git://git@bitbucket.org/Red_M/redssh.git`


# Documentation
99% of questions around how to do something should be answered in the documentation.
If something is not there please raise an issue so it can be added to the documentation.
[Now with autodocs!](https://redssh.readthedocs.io/en/latest/ "Documentation! :)")


# Why not use [other software]?

This is my experiences with other pieces of software to do something similar or the same as RedSSH.
It mostly revolves around compatibility with remote servers, (lack of) state(less) based automation or lack of features.

I've had issues with other software in the past and sometimes I found that other software doesn't want to do what I want it to do.
I should be able to open and close SSH tunnels at a whim, start up SCP/SFTP and access other lower level features of SSH at any time.

I've had issues with accessing non-Linux devices that have weird versions or custom compiles of the OpenSSH server or are completely custom SSH servers.
Because of incompatibility in other libraries, RedSSH isn't designed with just Linux in mind, its meant to control everything you can think of that has SSH.
If you can connect to it via your regular OpenSSH client then RedExpect/RedSSH should be able to connect as well.

I don't want to install an agent or have to manage state of a remote machine, if I want something done it should just be applied,
I don't want extra things to manage or leave hanging around.


# TO DO
- Unit tests
- More examples

