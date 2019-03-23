# RedSSH
# Copyright (C) 2018  Red_M ( http://bitbucket.com/Red_M )

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




# forward.py from paramiko
# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

# rforward.py from paramiko
# Copyright (C) 2008  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

import socket
import select
import time

from ssh2.session import LIBSSH2_SESSION_BLOCK_INBOUND, LIBSSH2_SESSION_BLOCK_OUTBOUND

try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer

class ForwardServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


class ForwardHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        itc = None
        try:
            itc = self.queue.get(False)
        except Exception as e:
            pass
        if itc=='terminate':
            return()
        try:
            peer = self.request.getpeername()
            chan = self.caller._block(self.caller.session.direct_tcpip_ex, self.dst_tup[0], self.dst_tup[1], self.src_tup[0], self.src_tup[1])
        except Exception as e:
            return()

        i = None
        while True:
            try:
                itc = self.queue.get(False)
            except Exception as e:
                pass
            if itc=='terminate':
                break
            (r, w, x) = select.select([self.request, self.caller.sock], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data)==0:
                    if i==None:
                        i = time.time()+self.sock_timeout
                    else:
                        if i<time.time():
                            break
                    time.sleep(0.005)
                    continue
                self.caller._block_write(chan.write,data)
            if self.caller.sock in r:
                for buf in self.caller._read_iter(chan.read,0.01):
                    self.request.send(buf)

        self.caller._block(chan.close)
        self.request.close()


def reverse_handler(chan, host, port):
    sock = socket.socket()
    try:
        sock.connect((host, port))
    except Exception as e:
        return

    while True:
        (r, w, x) = select.select([sock, chan], [], [])
        if sock in r:
            data = sock.recv(1024)
            if len(data) == 0:
                break
            chan.send(data)
        if chan in r:
            data = chan.recv(1024)
            if len(data) == 0:
                break
            sock.send(data)
    chan.close()
    sock.close()

