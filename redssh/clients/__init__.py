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
.. module:: redssh.clients
   :platform: Unix
   :synopsis: Provides SSH clients to the RedSSH SSH layer.

.. moduleauthor:: Red_M <redssh_docs@red-m.net>


'''
from redssh.enums import SSHClient

VERSION = u'1.0.0'

enabled_clients = {}


try:
   import redssh.clients.libssh as libssh
   enabled_clients[SSHClient.libssh] = libssh.LibSSH
   default_client = SSHClient.libssh
except:
   pass

try:
   import redssh.clients.libssh2 as libssh2
   enabled_clients[SSHClient.libssh2] = libssh2.LibSSH2
   default_client = SSHClient.libssh2
except:
   pass

