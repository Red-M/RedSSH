# RedSSH
# Copyright (C) 2018 - 2020  Red_M ( http://bitbucket.com/Red_M )

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
Just rebinding ssh2-python into a slightly nicer format.
'''

from ssh2.session import Session
from ssh2.session import LIBSSH2_HOSTKEY_HASH_SHA1,LIBSSH2_HOSTKEY_TYPE_RSA
from ssh2.knownhost import LIBSSH2_KNOWNHOST_TYPE_PLAIN,LIBSSH2_KNOWNHOST_KEYENC_RAW,LIBSSH2_KNOWNHOST_KEY_SSHRSA,LIBSSH2_KNOWNHOST_KEY_SSHDSS
from ssh2.session import LIBSSH2_SESSION_BLOCK_INBOUND,LIBSSH2_SESSION_BLOCK_OUTBOUND
from ssh2.error_codes import LIBSSH2_ERROR_EAGAIN
from ssh2.sftp import LIBSSH2_SFTP_S_IFMT,LIBSSH2_SFTP_S_IFIFO,LIBSSH2_SFTP_S_IFCHR,LIBSSH2_SFTP_S_IFDIR,LIBSSH2_SFTP_S_IFBLK,LIBSSH2_SFTP_S_IFREG,LIBSSH2_SFTP_S_IFLNK,LIBSSH2_SFTP_S_IFSOCK
from ssh2.sftp import LIBSSH2_FXF_READ,LIBSSH2_FXF_WRITE,LIBSSH2_FXF_APPEND,LIBSSH2_FXF_CREAT,LIBSSH2_FXF_TRUNC,LIBSSH2_FXF_EXCL
from ssh2.sftp import LIBSSH2_SFTP_S_IRWXU,LIBSSH2_SFTP_S_IRUSR,LIBSSH2_SFTP_S_IWUSR,LIBSSH2_SFTP_S_IXUSR,LIBSSH2_SFTP_S_IRWXG,LIBSSH2_SFTP_S_IRGRP,LIBSSH2_SFTP_S_IWGRP,LIBSSH2_SFTP_S_IXGRP,LIBSSH2_SFTP_S_IRWXO,LIBSSH2_SFTP_S_IROTH,LIBSSH2_SFTP_S_IWOTH,LIBSSH2_SFTP_S_IXOTH,LIBSSH2_SFTP_ST_RDONLY,LIBSSH2_SFTP_ST_NOSUID
from ssh2.sftp_handle import SFTPAttributes
import ssh2.exceptions as exceptions
try:
    # This is awful, fix it.
    # The fix for this is in my fork of ssh2-python
    from ssh2.session import LIBSSH2_METHOD_KEX, LIBSSH2_METHOD_HOSTKEY, \
    LIBSSH2_METHOD_CRYPT_CS, LIBSSH2_METHOD_CRYPT_SC, LIBSSH2_METHOD_MAC_CS, \
    LIBSSH2_METHOD_MAC_SC, LIBSSH2_METHOD_COMP_CS, LIBSSH2_METHOD_COMP_SC, \
    LIBSSH2_METHOD_LANG_CS, LIBSSH2_METHOD_LANG_SC, LIBSSH2_FLAG_SIGPIPE, \
    LIBSSH2_FLAG_COMPRESS
    from ssh2.session import LIBSSH2_CALLBACK_X11
except:
    pass
