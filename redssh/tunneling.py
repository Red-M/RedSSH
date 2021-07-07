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
import traceback
import struct
import socket
import threading
import multiprocessing

from redssh import enums
from redssh import libssh2

try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer


def check_closed(ssh_session,chan=None): # Macro for tunnel checks.
    return(ssh_session.check_closed(chan))


class LocalPortServer(SocketServer.ThreadingMixIn,SocketServer.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self,bind_arg,handler,caller,terminate,remote_host,remote_port,wchan,error_level):
        self.ssh_session = caller
        self.terminate = terminate
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.wchan = wchan
        self.error_level = error_level
        self.auto_terminate = bool(self.ssh_session.auto_terminate_tunnels)
        self.socks_server = (self.remote_host==None and self.remote_port==None)
        self.socks_version = 5
        self._select_tun_timeout = float(self.ssh_session._select_tun_timeout)
        super().__init__(bind_arg,handler)

    def server_activate(self):
        self.wchan.set()
        self.socket.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,self.ssh_session.tcp_nodelay)
        self.socket.listen(self.request_queue_size)

    def handle_error(self,request,client_address):
        error_level = self.error_level
        if error_level==enums.TunnelErrorLevel.warn:
            print('Exception happened during processing of request from',client_address,file=sys.stderr)
        if error_level==enums.TunnelErrorLevel.debug:
            print('Exception happened during processing of request from',client_address,file=sys.stderr)
            print(traceback.print_exc(),file=sys.stderr)
        elif error_level==enums.TunnelErrorLevel.error:
            super().handle_error(request,client_address)
        if self.auto_terminate==True:
            self.terminate.set()
        self.close_request(request)
        if self.auto_terminate==True:
            self.shutdown()


class LocalPortServerHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        try:
            if self.server.socks_server==False and check_closed(self.ssh_session)==False:
                local_handler(self.ssh_session,self.terminate,self.request,self.server.remote_host,self.server.remote_port,self.server._select_tun_timeout)
            elif self.server.socks_server==True and check_closed(self.ssh_session)==False:
                # https://github.com/rushter/socks5
                header = self.request.recv(2)
                version, nmethods = struct.unpack("!BB", header)
                assert version == self.server.socks_version
                assert nmethods > 0
                methods = self.get_available_methods(nmethods)
                self.request.sendall(struct.pack("!BB", self.server.socks_version, 0))
                version, cmd, _, address_type = struct.unpack("!BBBB", self.request.recv(4))
                assert version == self.server.socks_version
                if address_type == 1:  # IPv4
                    address = socket.inet_ntoa(self.request.recv(4))
                elif address_type == 3:  # Domain name
                    # domain_length = ord(self.request.recv(1)[0])
                    domain_length = self.request.recv(1)[0]
                    address = self.request.recv(domain_length)
                port = struct.unpack('!H', self.request.recv(2))[0]
                try:
                    if cmd == 1:  # CONNECT
                        remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        remote.connect((address, port))
                        bind_address = remote.getsockname()
                    else:
                        self.server.close_request(self.request)
                    c_addr = struct.unpack("!I", socket.inet_aton(bind_address[0]))[0]
                    c_port = bind_address[1]
                    reply = struct.pack("!BBBBIH", self.server.socks_version, 0, 0, address_type, c_addr, c_port)
                except Exception as err:
                    self.handle_error(self.request,self.request.getpeername())
                    reply = self.generate_failed_reply(address_type, 5)
                self.request.sendall(reply)
                if reply[1] == 0 and cmd == 1:
                    local_handler(self.ssh_session,self.terminate,self.request,address,port,self.server._select_tun_timeout)
                else:
                    self.server.close_request(self.request)
        finally:
            if self.terminate.is_set()==True or check_closed(self.ssh_session,self.ssh_session.channel)==True:
                self.server.shutdown()

    def get_available_methods(self, n):
        methods = []
        for i in range(n):
            methods.append(ord(self.request.recv(1)))
        return methods

    def generate_failed_reply(self, address_type, error_number):
        return(struct.pack("!BBBBIH", self.server.socks_version, error_number, 0, address_type, 0, 0))


def local_handler(ssh_session,terminate,request,remote_host,remote_port,_select_timeout):
    chan = ssh_session._block(ssh_session.session.direct_tcpip_ex,remote_host,remote_port,*request.getpeername(),_select_timeout=_select_timeout)
    # chan_eof = False
    while terminate.is_set()==False and check_closed(ssh_session,chan)==False:
        (r,w,x) = select.select([request,ssh_session.sock],[],[],_select_timeout)
        no_data = False
        if terminate.is_set()==True:
            no_data = True
            break
        for buf in ssh_session._read_iter(chan.read,_select_timeout=_select_timeout):
            if request.send(buf)<=0 or check_closed(ssh_session,chan)==True or terminate.is_set()==True:
                no_data = True
                break
        if no_data==True:
            break
        if request in r and terminate.is_set()==False and check_closed(ssh_session,chan)==False:
            if ssh_session._block_write(chan.write,request.recv(4096),_select_timeout=_select_timeout)<=0 or terminate.is_set()==True:
                break
        # chan_eof = ssh_session._block(chan.eof)
        if terminate.is_set()==True or check_closed(ssh_session,chan)==True:
            break

    if terminate.is_set()==True and chan.eof()==False:
        ssh_session._block(chan.close)
    request.close()






def remote_tunnel_server(ssh_session,host,port,bind_addr,local_port,terminate,wait_for_chan,error_level):
    _select_timeout = float(ssh_session._select_tun_timeout)
    auto_terminate = bool(ssh_session.auto_terminate_tunnels)
    listener = ssh_session._block(ssh_session.session.forward_listen_ex,bind_addr,local_port,0,1024)
    wait_for_chan.set()
    threads = []
    while terminate.is_set()==False and check_closed(ssh_session)==False:
        error = False
        try:
            with ssh_session._block_lock:
                chan = listener.forward_accept()
            while chan==libssh2.LIBSSH2_ERROR_EAGAIN and terminate.is_set()==False:
                ssh_session._block_select(_select_timeout)
                with ssh_session._block_lock:
                    if terminate.is_set()==False:
                        chan = listener.forward_accept()
        except libssh2.exceptions.ChannelUnknownError:
            error = True
            break
        if terminate.is_set()==True:
            break
        if error==False and terminate.is_set()==False:
            thread = threading.Thread(target=remote_handle,args=(ssh_session,chan,host,port,terminate,error_level,auto_terminate,_select_timeout))
            thread.name = 'remote_handle'
            threads.append(thread)
            thread.start()
    terminate.wait()
    for thread in threads:
        thread.join()


def remote_handle(ssh_session,chan,host,port,terminate,error_level,auto_terminate,_select_timeout):
    chan_eof = False
    try:
        request = socket.create_connection((host,port))
        request.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,ssh_session.tcp_nodelay)
    except Exception as e:
        ssh_session._block(chan.close,_select_timeout=_select_timeout)
        return()
    (r,w,x) = select.select([ssh_session.sock],[],[],_select_timeout)
    if ssh_session.sock in r:
        for buf in ssh_session._read_iter(chan.read,_select_timeout=_select_timeout):
            if request.send(buf)<=0:
                request.close()
                return()
    while terminate.is_set()==False and chan_eof!=True:
        (r,w,x) = select.select([ssh_session.sock,request],[],[],_select_timeout)
        if terminate.is_set()==True:
            request.close()
            ssh_session._block(chan.close,_select_timeout=_select_timeout)
            return()
        no_data = False

        for buf in ssh_session._read_iter(chan.read,_select_timeout=_select_timeout):
            if request.send(buf)<=0:
                no_data = True
                request.close()
                break
        if no_data==True:
            break
        if request in r:
            if ssh_session._block_write(chan.write,request.recv(4096),_select_timeout=_select_timeout)<=0:
                break
        chan_eof = check_closed(ssh_session,chan)
    request.close()
    if auto_terminate==True:
        ssh_session._block(chan.close,_select_timeout=_select_timeout)


