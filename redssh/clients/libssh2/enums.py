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

class LibSSH2Client(enum.Enum):
    eagain = libssh2.enums.ErrorCodes.EAGAIN
    auth_eagain = libssh2.enums.ErrorCodes.EAGAIN
    eof = libssh2.enums.ErrorCodes.CHANNEL_EOF_SENT
    class exceptions(enum.Enum):
        EOF = libssh2.exceptions.ChannelEOFSentError
    class Poll(enum.Enum):
        read = libssh2.enums.Session.BLOCK_INBOUND
        write = libssh2.enums.Session.BLOCK_OUTBOUND
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
