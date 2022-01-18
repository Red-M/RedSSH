# RedSSH
# Copyright (C) 2022 - 2022 Red_M ( http://bitbucket.com/Red_M )

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
import enum
from . import libssh
from redssh.clients.libssh2 import libssh2

class Client(enum.IntEnum):
    eagain = libssh.enums.SSH.AGAIN.value
    auth_eagain = libssh.enums.Auth.AGAIN.value
    eof = libssh.enums.SSH.EOF.value
class Exceptions(enum.Enum):
    EOF = libssh.exceptions.EOF
class Poll(enum.IntEnum):
    read = libssh.enums.SSH.READ_PENDING.value
    write = libssh.enums.SSH.WRITE_PENDING.value
class Channel(enum.Enum):
    setenv = 'request_env' # TODO set more channel methods below.
    request_pty = 'request_pty'
    exec_command = 'request_exec'
    get_exit_status = 'get_exit_status'
    read = 'read_nonblocking'
    write = 'write'
    flush = 'flush'
    send_eof = 'send_eof'
    close = 'close'
class SFTP(enum.IntEnum):
    DEFAULT_WRITE_MODE = libssh.enums.SFTP_AT.O_RDWR | libssh.enums.SFTP_AT.O_CREAT | libssh.enums.SFTP_AT.O_TRUNC
    DEFAULT_READ_MODE = libssh.enums.SFTP_AT.O_RDONLY
    DEFAULT_FILE_MODE = 0o664
class SFTP_S(enum.IntEnum):
    # File mode masks
    # Read, write, execute/search by owner
   IRWXU = libssh2.enums.SFTP.S_IRWXU.value
   IRUSR = libssh2.enums.SFTP.S_IRUSR.value
   IWUSR = libssh2.enums.SFTP.S_IWUSR.value
   IXUSR = libssh2.enums.SFTP.S_IXUSR.value
    # Read, write, execute/search by group
   IRWXG = libssh2.enums.SFTP.S_IRWXG.value
   IRGRP = libssh2.enums.SFTP.S_IRGRP.value
   IWGRP = libssh2.enums.SFTP.S_IWGRP.value
   IXGRP = libssh2.enums.SFTP.S_IXGRP.value
    # Read, write, execute/search by others
   IRWXO = libssh2.enums.SFTP.S_IRWXO.value
   IROTH = libssh2.enums.SFTP.S_IROTH.value
   IWOTH = libssh2.enums.SFTP.S_IWOTH.value
   IXOTH = libssh2.enums.SFTP.S_IXOTH.value
