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
.. module:: redssh
   :platform: Unix
   :synopsis: Offers the RedSSH SSH layer.

.. moduleauthor:: Red_M <redssh_docs@red-m.net>


'''
VERSION = u'3.0.0'

from .redssh import RedSSH
from . import clients
from .clients.libssh2 import libssh2
from .clients.libssh import libssh
from . import exceptions
from . import enums

