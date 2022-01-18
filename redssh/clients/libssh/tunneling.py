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
import traceback
import struct
import socket
import threading
import multiprocessing

import ssh

from redssh import enums
from redssh.clients.libssh import libssh

try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer


def handle_sock_xfer(ssh_session, sock, to_read, self_index, other_index):
    if ssh_session.session.check_c_poll_enabled()==True:
        return((to_read[self_index] & ssh.utils.pollin)==1 or (to_read[other_index] & ssh.utils.pollin)==0)
    else:
        return(sock in to_read)

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
            self.request.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,self.ssh_session.tcp_nodelay)
            if self.server.socks_server==False:
                local_handler(self.ssh_session,self.terminate,self.request,self.server.remote_host,self.server.remote_port,self.server._select_tun_timeout)
            elif self.server.socks_server==True:
                # https://github.com/rushter/socks5
                header = self.request.recv(2)
                version, nmethods = struct.unpack("!BB", header)
                if not (version == self.server.socks_version and nmethods > 0):
                    reply = self.generate_failed_reply(address_type, 5)
                    self.request.sendall(reply)
                    return()
                methods = self.get_available_methods(nmethods)
                self.request.sendall(struct.pack("!BB", self.server.socks_version, 0))
                version, cmd, _, address_type = struct.unpack("!BBBB", self.request.recv(4))
                if version != self.server.socks_version:
                    reply = self.generate_failed_reply(address_type, 5)
                    self.request.sendall(reply)
                    return()
                if address_type == 1:  # IPv4
                    address = socket.inet_ntoa(self.request.recv(4))
                elif address_type == 3:  # Domain name
                    # domain_length = ord(self.request.recv(1)[0])
                    domain_length = self.request.recv(1)[0]
                    address = self.request.recv(domain_length)
                port = struct.unpack('!H', self.request.recv(2))[0]
                if cmd == 1:  # CONNECT
                    self.request.sendall(struct.pack("!BBBBIH", self.server.socks_version, 0, 0, 1, 0, 0))
                    local_handler(self.ssh_session,self.terminate,self.request,address,port,self.server._select_tun_timeout)
                else:
                    self.handle_error(self.request,self.request.getpeername())
                    reply = self.generate_failed_reply(address_type, 5)
        finally:
            self.server.close_request(self.request)
            if self.terminate.is_set()==True:
                self.server.shutdown()

    def get_available_methods(self, n):
        methods = []
        for i in range(n):
            methods.append(ord(self.request.recv(1)))
        return methods

    def generate_failed_reply(self, address_type, error_number):
        return(struct.pack("!BBBBIH", self.server.socks_version, error_number, 0, address_type, 0, 0))


def local_handler(ssh_session,terminate,request,remote_host,remote_port,_select_timeout):
    chan = ssh_session.open_channel(False)
    ssh_session._block(chan.open_forward,remote_host,remote_port,*request.getpeername(),_select_timeout=_select_timeout)
    tun = ssh.tunnel.Tunnel(ssh_session.session,chan,request)
    # chan_eof = False
    while terminate.is_set()==False:
        (r,w,x) = tun._block_call(10)
        no_data = False
        if handle_sock_xfer(ssh_session, ssh_session.session.sock, r, 0, 1)==True and terminate.is_set()==False:
            for buf in ssh_session._read_iter(chan.read_nonblocking,_select_timeout=_select_timeout):
                if request.send(buf)<=0 or terminate.is_set()==True:
                    no_data = True
                    break
        if no_data==True or terminate.is_set()==True:
            break
        if handle_sock_xfer(ssh_session, request, r, 1, 0)==True and terminate.is_set()==False:
            try:
                if ssh_session._block_write(chan.write,request.recv(4096,socket.MSG_DONTWAIT),_select_timeout=_select_timeout)<=0 or terminate.is_set()==True:
                    no_data = True
                    break
            except:
                pass
        if no_data==True or terminate.is_set()==True:
            break

    # if terminate.is_set()==True and chan.eof()==False:
        # ssh_session._block(chan.close)
    del tun, chan
    request.close()




def remote_tunnel_server(ssh_session,host,port,bind_addr,local_port,terminate,wait_for_chan,error_level):
    _select_timeout = float(ssh_session._select_tun_timeout)
    auto_terminate = bool(ssh_session.auto_terminate_tunnels)
    ssh_session._block(ssh_session.session.listen_forward,bind_addr,local_port,port)
    wait_for_chan.set()
    threads = []
    while terminate.is_set()==False:
        error = False
        try:
            with ssh_session.session._block_lock:
                chan = ssh_session.session.accept_forward(1,0)
            time.sleep(_select_timeout*50)
            while chan==None and terminate.is_set()==False:
                ssh_session._block_select(_select_timeout)
                with ssh_session.session._block_lock:
                    if terminate.is_set()==False:
                        chan = ssh_session.session.accept_forward(1,0)
                time.sleep(_select_timeout*50)
        except Exception as e:
            print(e)
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
    try:
        request = socket.create_connection((host,port))
        request.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,ssh_session.tcp_nodelay)
    except Exception as e:
        ssh_session._block(chan.close,_select_timeout=_select_timeout)
        return()
    tun = ssh.tunnel.Tunnel(ssh_session.session,chan,request)
    (r,w,x) = tun._block_call(10)
    if handle_sock_xfer(ssh_session, ssh_session.session.sock, r, 0, 1)==True:
        for buf in ssh_session._read_iter(chan.read_nonblocking,_select_timeout=_select_timeout):
            if request.send(buf)<=0:
                request.close()
                return()
    while terminate.is_set()==False:
        (r,w,x) = tun._block_call(10)
        no_data = False

        if terminate.is_set()==False:
            for buf in ssh_session._read_iter(chan.read_nonblocking,_select_timeout=_select_timeout):
                if request.send(buf)<=0:
                    request.close()
                    no_data = True
                    break
        if no_data==True or terminate.is_set()==True:
            break
        if handle_sock_xfer(ssh_session, request, r, 1, 0)==True and terminate.is_set()==False:
            try:
                if ssh_session._block_write(chan.write,request.recv(4096,socket.MSG_DONTWAIT),_select_timeout=_select_timeout)<=0:
                    no_data = True
                    break
            except:
                pass
        if no_data==True or terminate.is_set()==True:
            break

    request.close()
    if auto_terminate==True:
        ssh_session._block(chan.close,_select_timeout=_select_timeout)


