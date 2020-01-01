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
import enum

class SSHHostKeyVerify(enum.Enum):
    strict = 0
    warn = 1
    warn_auto_add = 2
    auto_add = 3
    none = 4

class TunnelType(enum.Enum):
    local = 'local'
    remote = 'remote'
    dynamic = 'dynamic'
    x11 = 'X11'

class TunnelErrorLevel(enum.Enum):
    none = 0
    warn = 1
    debug = 2
    error = 3
