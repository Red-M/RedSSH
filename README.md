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

I've found other automation libraries or solutions lacking, such as:
- Compatibility with remote servers (odd servers causes the library to be unable to connect).
- Feature set is limited (eg, no tunneling).
- Focuses on only connecting to Linux servers.
- Requires an agent to be installed, a state file to be present or a master "server".
- Poor performance.


# TO DO
- Unit tests
- Host based authentication
- Host key checking
- More examples
- SCP
- X11 forwarding

