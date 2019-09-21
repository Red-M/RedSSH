# RedSSH
# Copyright (C) 2019  Red_M ( http://bitbucket.com/Red_M )

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




# forward.py from paramiko
# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License,or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful,but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not,write to the Free Software Foundation,Inc.,
# 59 Temple Place,Suite 330,Boston,MA  02111-1307  USA.

# rforward.py from paramiko
# Copyright (C) 2008  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License,or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful,but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not,write to the Free Software Foundation,Inc.,
# 59 Temple Place,Suite 330,Boston,MA  02111-1307  USA.

import socket
import select
import time

from ssh2.session import LIBSSH2_SESSION_BLOCK_INBOUND,LIBSSH2_SESSION_BLOCK_OUTBOUND
from ssh2.error_codes import LIBSSH2_ERROR_EAGAIN

try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer

class ForwardServer(SocketServer.ThreadingMixIn,SocketServer.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


class ForwardHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        i = None
        while self.terminate.is_set()==False or self.chan.eof()==True:
            (r,w,x) = select.select([self.request,self.caller.sock],[],[])
            if self.terminate.is_set()==True or self.chan.eof()==True:
                break
            if self.request in r:
                data = self.request.recv(1024)
                if len(data)==0:
                    break
                self.caller._block_write(self.chan.write,data)
            if self.caller.sock in r:
                for buf in self.caller._read_iter(self.chan.read,self.caller.ssh_wait_time_window):
                    self.request.send(buf)

        if not self.chan.eof():
            self.caller._block(self.chan.close)
        self.request.close()


def reverse_handler(self,listener,host,port,local_port,queue):
    while True:
        chan = listener.forward_accept()
        if not chan==LIBSSH2_ERROR_EAGAIN:
            break
        elif chan==LIBSSH2_ERROR_EAGAIN:
            self._block_select(1)
    try:
        request = socket.create_connection((host,port))
    except Exception as e:
        return()

    while True:
        itc = None
        try:
            itc = queue.get(False)
        except Exception as e:
            pass
        if itc=='terminate' or chan.eof():
            break
        print(1)
        (r,w,x) = select.select([self.sock,request],[],[])
        if request in r:
            data = request.recv(1024)
            if len(data)==0:
                break
            print('request')
            self._block_write(chan.write,data)
        if self.sock in r:
            print('sock')
            for buf in self._read_iter(chan.read,self.caller.ssh_wait_time_window):
                request.send(buf)
    if not chan.eof():
        self._block(chan.close)
    request.close()


