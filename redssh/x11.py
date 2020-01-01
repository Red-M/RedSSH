# RedSSH
# Copyright (C) 2018 - 2020  Red_M ( http://bitbucket.com/Red_M )

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License,or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not,write to the Free Software Foundation,Inc.,
# 51 Franklin Street,Fifth Floor,Boston,MA 02110-1301 USA.


import sys
import time
import select
import struct

from redssh import enums
from redssh import libssh2


# def forward(self,terminate):
    # while terminate.is_set()==False:
        # (r,w,x) = select.select([self.sock for self.sock, _ in self.x11_channels], [], [], self._select_tun_timeout)

        # for self.sock, x11_chan in list(self.x11_channels):
            # for buf in self._read_iter(x11_chan.read):
                # self._block_write(self.channel.send,data)

            # if self.sock in r:
                # for buf in self._read_iter(self.channel.read):
                    # if buf is None:
                        # self.x11_channels.remove((x11_chan, self.sock))
                    # else:
                        # x11_chan.write(buf)

            # if x11_chan.eof():
                # self.x11_channels.remove((self.sock, x11_chan))
                # continue

        # if terminate.is_set()==True or self.channel.eof()==True:
            # break

