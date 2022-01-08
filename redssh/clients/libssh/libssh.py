# RedSSH
# Copyright (C) 2018 - 2022 Red_M ( http://bitbucket.com/Red_M )

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''
Just rebinding ssh-python into a slightly nicer format.
'''
from ssh import exceptions
from ssh.session import Session, SSH_READ_PENDING, SSH_WRITE_PENDING, SSH_AUTH_SUCCESS, SSH_AUTH_DENIED, SSH_AUTH_PARTIAL, SSH_AUTH_INFO, SSH_AUTH_AGAIN, SSH_AUTH_ERROR
from ssh import scp
from ssh import sftp
# from ssh import c_ssh
# from ssh import c_ssh2
from ssh import options
from ssh import error_codes

