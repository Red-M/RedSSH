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
from . import libssh2

class Client(enum.IntEnum):
    eagain = libssh2.enums.ErrorCodes.EAGAIN.value
    auth_eagain = libssh2.enums.ErrorCodes.EAGAIN.value
    eof = libssh2.enums.ErrorCodes.CHANNEL_EOF_SENT.value

class Exceptions(enum.Enum):
    EOF = libssh2.exceptions.ChannelEOFSentError

class Poll(enum.IntEnum):
    read = libssh2.enums.Session.BLOCK_INBOUND.value
    write = libssh2.enums.Session.BLOCK_OUTBOUND.value

class Channel(enum.Enum):
    setenv = 'setenv' # TODO set more channel methods below.
    request_pty = 'pty'
    exec_command = 'request_exec'
    get_exit_status = 'get_exit_status'
    read = 'read_nonblocking'
    write = 'write'
    flush = 'flush'
    send_eof = 'send_eof'
    close = 'close'

class SFTP(enum.IntEnum):
    DEFAULT_WRITE_MODE = libssh2.LIBSSH2_FXF_WRITE | libssh2.LIBSSH2_FXF_CREAT | libssh2.LIBSSH2_FXF_TRUNC
    DEFAULT_READ_MODE = libssh2.LIBSSH2_FXF_READ
    DEFAULT_FILE_MODE = libssh2.LIBSSH2_SFTP_S_IRUSR | libssh2.LIBSSH2_SFTP_S_IWUSR | libssh2.LIBSSH2_SFTP_S_IRGRP | libssh2.LIBSSH2_SFTP_S_IWGRP | libssh2.LIBSSH2_SFTP_S_IROTH

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


