Contributing
===========

Please sumbit all changes as pull requests on either bitbucket or github.

Changes that do not pass the test suite or lower code coverage in the area of the change will not be accepted.
Do note that due to the nature of how this library is working, even between 2 runs of the test suite, coverage can lower
because of the way that `redssh.RedSSH._block()`, `redssh.RedSSH._block_write()`, `redssh.RedSSH._read_iter()` and `redssh.RedSSH._block_select()`
execute.

Changes need to have a good reason to change current functionality and will be weighted up based on merrit of the change to the library,
however, changes that add new features will only require that the change adds something useful to the library.

Please note this file is currently a work in progress.
