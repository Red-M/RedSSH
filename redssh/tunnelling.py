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


import multiprocessing
import threading
import socket
import select
import time

from redssh import libssh2

try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer

class LocalPortServer(SocketServer.ThreadingMixIn,SocketServer.TCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self,bind_arg,handler,caller,remote_host,remote_port,wchan):
        self.caller = caller
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.wchan = wchan
        self.wchan_lock = multiprocessing.Lock()
        super().__init__(bind_arg,handler)

    def server_activate(self):
        self.chan = self.caller._block(self.caller.session.direct_tcpip,self.remote_host,self.remote_port)
        self.wchan.set()
        self.socket.listen(self.request_queue_size)


class LocalPortHandler(SocketServer.BaseRequestHandler):

    def _ssh_block(self,func,*args,**kwargs):
        self.server.wchan_lock.acquire()
        response = self.caller._block(func,*args,**kwargs)
        self.server.wchan_lock.release()
        return(response)

    def _ssh_block_write(self,func,data,timeout=None):
        self.server.wchan_lock.acquire()
        self.caller._block_write(func,data,timeout=timeout)
        self.server.wchan_lock.release()

    def _ssh_read_iter(self,func,timeout=None):
        self.server.wchan_lock.acquire()
        response = self.caller._read_iter(func,timeout=timeout)
        self.server.wchan_lock.release()
        return(response)


    def handle(self):
        try:
            while self.terminate.is_set()==False and self._ssh_block(self.server.chan.eof)==False:
                (r,w,x) = select.select([self.request,self.caller.sock],[],[],self.caller.ssh_wait_time_window)
                if self.terminate.is_set()==True or self._ssh_block(self.server.chan.eof)==True:
                    break
                if self.request in r and self.terminate.is_set()==False:
                    data = self.request.recv(1024)
                    if len(data)==0:
                        break
                    self._ssh_block_write(self.server.chan.write,data)
                if self.caller.sock in r and self.terminate.is_set()==False:
                    for buf in self._ssh_read_iter(self.server.chan.read,self.caller.ssh_wait_time_window):
                        self.request.send(buf)
                if self.terminate.is_set()==True or self._ssh_block(self.server.chan.eof)==True:
                    break
            self.request.close()
        finally:
            if self.terminate.is_set()==True:
                self.server.shutdown()



def remote_handler(self,host,port,bind_addr,local_port,terminate,wait_for_chan):
    listener = self._block(self.session.forward_listen_ex,bind_addr,local_port,0,1024)
    wait_for_chan.set()
    while terminate.is_set()==False and self._block(self.channel.eof)==False:
        try:
            chan = listener.forward_accept()
            # print('chan_init')
        except:
            continue
        if chan==libssh2.LIBSSH2_ERROR_EAGAIN:
            self._block_select(self.ssh_wait_time_window)
        else:
            try:
                req_wait_calc = time.time()
                request = socket.create_connection((host,port))
                req_wait = time.time()-req_wait_calc
            except Exception as e:
                self._block(chan.close)
                return()
            for buf in self._read_iter(chan.read,req_wait):
                request.send(buf)
            while terminate.is_set()==False and self._block(chan.eof)==False:
                # print('sel1')
                (r,w,x) = select.select([self.sock,request],[],[],req_wait)
                # print('sel2')
                if terminate.is_set()==True or self._block(chan.eof)==True:
                    return()
                if self.sock in r:
                    sent = 0
                    for buf in self._read_iter(chan.read,req_wait):
                        request.send(buf)
                        sent+=len(buf)
                        if terminate.is_set()==True or self._block(chan.eof)==True:
                            break
                    if terminate.is_set()==True or self._block(chan.eof)==True:
                        return()
                    if sent==0:
                        # print('chan_break')
                        break
                if request in r:
                    # print('req')
                    data = request.recv(1024)
                    self._block_write(chan.write,data)
                    if len(data)==0:
                        # print('req_break')
                        break
            # print('term')
            self._block(chan.close)
            break




