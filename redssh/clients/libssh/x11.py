# RedSSH
# Copyright (C) 2018 - 2022 Red_M ( http://bitbucket.com/Red_M )

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
from . import libssh


# def forward(self,display_number,terminate):
    # _select_timeout = float(self._select_tun_timeout)
    # auto_terminate = bool(self.auto_terminate_tunnels)
    # self._block(self.channel.request_x11, display_number, False)
    # wait_for_chan.set()
    # threads = []
    # while terminate.is_set()==False:
        # error = False
        # try:
            # with self.session._block_lock:
                # chan = self.channel.accept_x11(1)
            # time.sleep(_select_timeout*50)
            # while chan==None and terminate.is_set()==False:
                # self._block_select(_select_timeout)
                # with self.session._block_lock:
                    # if terminate.is_set()==False:
                        # chan = self.channel.accept_x11(1)
                # time.sleep(_select_timeout*50)
        # except Exception as e:
            # print(e)
            # error = True
            # break
        # if terminate.is_set()==True:
            # break
        # if error==False and terminate.is_set()==False:
            # thread = threading.Thread(target=x11_handle,args=(self,chan,terminate,error_level,auto_terminate,_select_timeout))
            # thread.name = 'x11_handle'
            # threads.append(thread)
            # thread.start()
    # terminate.wait()
    # for thread in threads:
        # thread.join()

# def x11_handle(self,chan,terminate,error_level,auto_terminate,_select_timeout):
    # tun = ssh.tunnel.Tunnel(self.session,chan,request)
    # (r,w,x) = tun._block_call(_select_timeout)
    # if handle_sock_xfer(self, self.session.sock, r, 0, 1)==True:
        # for buf in self._read_iter(chan.read_nonblocking,_select_timeout=_select_timeout):
            # print(buf)
    # self._block(chan.close,_select_timeout=_select_timeout)
