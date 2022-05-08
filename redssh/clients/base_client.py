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

import os
import re
import enum
import threading
import multiprocessing

from redssh import exceptions
from redssh import enums

class BaseClientModules:
    client_enums = None
    scp = None
    sftp = None
    tunneling = None
    x11 = None

class BaseClient(object):
    '''
    Instances the start of an SSH connection.
    Extra options are available after :func:`redssh.RedSSH.connect` is called.

    :param encoding: Set the encoding to something other than the default of ``'utf8'`` when your target SSH server doesn't return UTF-8.
    :type encoding: ``str``
    :param terminal: Set the terminal sent to the remote server to something other than the default of ``'vt100'``.
    :type terminal: ``str``
    :param known_hosts: Set the known hosts file to a set location other than ``'~/.ssh/known_hosts'``, ``None`` is the default location.
    :type known_hosts: ``str``
    :param ssh_host_key_verification: Change the behaviour of remote host key verification. Can be set to one of the following values, ``strict``, ``warn``, ``auto_add`` or ``none``.
    :type ssh_host_key_verification: :class:`redssh.enums.SSHHostKeyVerify`
    :param ssh_keepalive_interval: Enable or disable SSH keepalive packets, value is interval in seconds, ``0`` is off.
    :type ssh_keepalive_interval: ``float``
    :param set_flags: Not supported in ssh2-python 0.18.0
    :type set_flags: ``dict``
    :param method_preferences: Not supported in ssh2-python 0.18.0
    :type method_preferences: ``dict``
    :param callbacks: Not supported yet
    :type callbacks: ``dict``
    :param auto_terminate_tunnels: Automatically terminate tunnels when errors are detected
    :type auto_terminate_tunnels: ``bool``
    :param tcp_nodelay: Set `TCP_NODELAY` for the underlying :func:`socket.socket`, by default this is off via `False`.
    :type tcp_nodelay: ``bool``
    '''
    def __init__(self,encoding='utf8',terminal='vt100',known_hosts=None,ssh_host_key_verification=enums.SSHHostKeyVerify.warn,ssh_keepalive_interval=0.0,auto_terminate_tunnels=False,tcp_nodelay=False):
        self.debug = False
        self.__shutdown_all__ = multiprocessing.Event()
        self.tcp_nodelay = tcp_nodelay
        self.terminal = terminal
        self.encoding = encoding
        self.request_pty = True
        self.tunnels = {
            enums.TunnelType.local:{},
            enums.TunnelType.remote:{},
            enums.TunnelType.dynamic:{},
            enums.TunnelType.x11:{}
        }
        self.auto_terminate_tunnels = auto_terminate_tunnels
        self._auto_select_timeout_enabled = True
        self._select_timeout = 0.005
        self._select_tun_timeout = 0.001
        self.ssh_keepalive_interval = ssh_keepalive_interval
        self.ssh_host_key_verification = ssh_host_key_verification
        if known_hosts==None:
            self.known_hosts_path = os.path.join(os.path.expanduser('~'),'.ssh','known_hosts')
        else:
            self.known_hosts_path = known_hosts
        self._modules = BaseClientModules
        self.enums = self._modules.client_enums
        self.past_login = False


    def __del__(self):
        self.exit()

    def __check_for_attr__(self,attr):
        return(attr in self.__dict__)

    def __shutdown_thread__(self,thread,queue,server):
        queue.set()
        if not server==None:
            server.shutdown()
        if thread.is_alive()==True:
            thread.join()

    def _block_select(self,_select_timeout=None):
        if _select_timeout==None:
            _select_timeout = self._select_timeout
        self.session._block_call(_select_timeout)

    def before_connect_options(self):
        pass

    def after_connect_options(self):
        pass

    def local_tunnel(self,local_port,remote_host,remote_port,bind_addr='127.0.0.1',error_level=enums.TunnelErrorLevel.warn):
        '''

        Forwards a port on the remote machine the same way the ``-L`` option does for the OpenSSH client.

        Providing a ``0`` for the local port will mean the OS will assign an unbound port for you.
        This port number will be provided to you by this function.

        :param local_port: The local port on the local machine to bind to.
        :type local_port: ``int``
        :param remote_host: The remote host to connect to via the remote machine.
        :type remote_host: ``str``
        :param remote_port: The remote host's port to connect to via the remote machine.
        :type remote_port: ``int``
        :param bind_addr: The bind address on this machine to bind to for the local port.
        :type bind_addr: ``str``
        :param error_level: The level of verbosity that errors in tunnel threads will use.
        :type error_level: :class:`redssh.enums.TunnelErrorLevel`
        :return: ``int`` The local port that has been bound.
        '''
        if isinstance(remote_host,type('')) and isinstance(remote_port,type(0)):
            option_string = str(bind_addr)+':'+str(local_port)+':'+remote_host+':'+str(remote_port)
            if not option_string in self.tunnels[enums.TunnelType.local]:
                wait_for_chan = threading.Event()
                thread_terminate = threading.Event()

                class SubHander(self._modules.tunneling.LocalPortServerHandler):
                    ssh_session = self
                    chain_host = remote_host
                    chain_port = remote_port
                    terminate = thread_terminate
                    wchan = wait_for_chan

                tun_server = self._modules.tunneling.LocalPortServer((bind_addr,local_port),SubHander,self,thread_terminate,remote_host,remote_port,wait_for_chan,error_level)
                tun_thread = threading.Thread(target=tun_server.serve_forever)
                tun_thread.daemon = True
                tun_thread.name = enums.TunnelType.local+':'+option_string
                tun_thread.start()
                wait_for_chan.wait()
                if local_port==0:
                    local_port = tun_server.socket.getsockname()[1]
                    option_string = str(bind_addr)+':'+str(local_port)+':'+remote_host+':'+str(remote_port)
                    tun_thread.name = enums.TunnelType.local+':'+option_string
                self.tunnels[enums.TunnelType.local][option_string] = (tun_thread,thread_terminate,tun_server,local_port)
            return(local_port)

    def remote_tunnel(self,local_port,remote_host,remote_port,bind_addr='127.0.0.1',error_level=enums.TunnelErrorLevel.warn):
        '''

        Forwards a port to the remote machine via the local machine the same way the ``-R`` option does for the OpenSSH client.

        :param local_port: The local port on the remote side for clients to connect to.
        :type local_port: ``int``
        :param remote_host: The remote host to connect to via the local machine.
        :type remote_host: ``str``
        :param remote_port: The remote host's port to connect to via the local machine.
        :type remote_port: ``int``
        :param error_level: The level of verbosity that errors in tunnel threads will use.
        :type error_level: :class:`redssh.enums.TunnelErrorLevel`
        :return: ``None``
        '''
        option_string = str(bind_addr)+':'+str(local_port)+':'+remote_host+':'+str(remote_port)
        if not option_string in self.tunnels[enums.TunnelType.remote]:
            wait_for_chan = threading.Event()
            thread_terminate = threading.Event()
            tun_thread = threading.Thread(target=self._modules.tunneling.remote_tunnel_server,args=(self,remote_host,remote_port,bind_addr,local_port,thread_terminate,wait_for_chan,error_level))
            tun_thread.daemon = True
            tun_thread.name = enums.TunnelType.remote+':'+option_string
            tun_thread.start()
            wait_for_chan.wait()
            self.tunnels[enums.TunnelType.remote][option_string] = (tun_thread,thread_terminate,None,None)
        return(None)

    def dynamic_tunnel(self,local_port,bind_addr='127.0.0.1',error_level=enums.TunnelErrorLevel.warn):
        '''

        Opens a SOCKS proxy AKA gateway or dynamic port the same way the ``-D`` option does for the OpenSSH client.

        Providing a ``0`` for the local port will mean the OS will assign an unbound port for you.
        This port number will be provided to you by this function.

        :param local_port: The local port on the local machine to bind to.
        :type local_port: ``int``
        :param bind_addr: The bind address on this machine to bind to for the local port.
        :type bind_addr: ``str``
        :param error_level: The level of verbosity that errors in tunnel threads will use.
        :type error_level: :class:`redssh.enums.TunnelErrorLevel`
        :return: ``int`` The local port that has been bound.
        '''
        option_string = bind_addr+':'+str(local_port)
        if not option_string in self.tunnels[enums.TunnelType.dynamic]:
            wait_for_chan = threading.Event()
            thread_terminate = threading.Event()

            class SubHander(self._modules.tunneling.LocalPortServerHandler):
                ssh_session = self
                chain_host = None
                chain_port = None
                terminate = thread_terminate
                wchan = wait_for_chan

            tun_server = self._modules.tunneling.LocalPortServer((bind_addr,local_port),SubHander,self,thread_terminate,None,None,wait_for_chan,error_level)
            tun_thread = threading.Thread(target=tun_server.serve_forever)
            tun_thread.daemon = True
            tun_thread.name = enums.TunnelType.dynamic+':'+option_string
            tun_thread.start()
            wait_for_chan.wait()
            if local_port==0:
                local_port = tun_server.socket.getsockname()[1]
                option_string = bind_addr+':'+str(local_port)
                tun_thread.name = enums.TunnelType.dynamic+':'+option_string
            self.tunnels[enums.TunnelType.dynamic][option_string] = (tun_thread,thread_terminate,tun_server,local_port)
        return(local_port)

    def tunnel_is_alive(self,tunnel_type,sport,rhost=None,rport=None,bind_addr='127.0.0.1'):
        '''

        Checks if a tunnel is alive.
        Provide the same arguments to this that was given for openning the tunnel.

        Examples:

        `local_tunnel(9999,'localhost',8888)` would be `tunnel_is_alive(redssh.enums.TunnelType.local,9999,'localhost',8888)`

        `remote_tunnel(7777,'localhost',8888)` would be `tunnel_is_alive(redssh.enums.TunnelType.remote,7777,'localhost',8888)`

        `dynamic_tunnel(9999)` would be `tunnel_is_alive(redssh.enums.TunnelType.dynamic,9999)`

        `dynamic_tunnel(9999,'10.0.0.1')` would be `tunnel_is_alive(redssh.enums.TunnelType.dynamic,9999,bind_addr='10.0.0.1')`

        :param tunnel_type: The tunnel type to shutdown.
        :type tunnel_type: :class:`redssh.enums.TunnelType`
        :param sport: The bound port for local and dynamic tunnels or the local port on the remote side for remote tunnels.
        :type sport: ``str``
        :param rhost: The remote host for local and remote tunnels.
        :type rhost: ``str``
        :param rport: The remote port for local and remote tunnels.
        :type rport: ``int``
        :param bind_addr: The bind address used for local and dynamic tunnels.
        :type bind_addr: ``str``
        :return: ``bool``, if bad tunnel type provided returns ``None``
        '''
        if tunnel_type in enums.TunnelType:
            if tunnel_type==enums.TunnelType.dynamic:
                option_string = bind_addr+':'+str(sport)
            elif rhost!=None and rport!=None:
                option_string = str(bind_addr)+':'+str(sport)+':'+rhost+':'+str(rport)
            else:
                return(False)
            if option_string in self.tunnels[tunnel_type]:
                (thread,queue,server,server_port) = self.tunnels[tunnel_type][option_string]
                return(thread.is_alive())

    def shutdown_tunnel(self,tunnel_type,sport,rhost=None,rport=None,bind_addr='127.0.0.1'):
        '''

        Closes an open tunnel.
        Provide the same arguments to this that was given for openning the tunnel.

        Examples:

        `local_tunnel(9999,'localhost',8888)` would be `shutdown_tunnel(redssh.enums.TunnelType.local,9999,'localhost',8888)`

        `remote_tunnel(7777,'localhost',8888)` would be `shutdown_tunnel(redssh.enums.TunnelType.remote,7777,'localhost',8888)`

        `dynamic_tunnel(9999)` would be `shutdown_tunnel(redssh.enums.TunnelType.dynamic,9999)`

        `dynamic_tunnel(9999,'10.0.0.1')` would be `shutdown_tunnel(redssh.enums.TunnelType.dynamic,9999,bind_addr='10.0.0.1')`

        :param tunnel_type: The tunnel type to shutdown.
        :type tunnel_type: :class:`redssh.enums.TunnelType`
        :param sport: The bound port for local and dynamic tunnels or the local port on the remote side for remote tunnels.
        :type sport: ``str``
        :param rhost: The remote host for local and remote tunnels.
        :type rhost: ``str``
        :param rport: The remote port for local and remote tunnels.
        :type rport: ``int``
        :param bind_addr: The bind address used for local and dynamic tunnels.
        :type bind_addr: ``str``
        :return: ``None``
        '''
        if tunnel_type in enums.TunnelType:
            if tunnel_type==enums.TunnelType.dynamic:
                option_string = bind_addr+':'+str(sport)
            elif rhost!=None and rport!=None:
                option_string = str(bind_addr)+':'+str(sport)+':'+rhost+':'+str(rport)
            else:
                return()
            if option_string in self.tunnels[tunnel_type]:
                (thread,queue,server,server_port) = self.tunnels[tunnel_type][option_string]
                self.__shutdown_thread__(thread,queue,server)
                del self.tunnels[tunnel_type][option_string]


    def close_tunnels(self):
        '''
        Closes all SSH tunnels if any are open.
        '''
        for thread_type in self.tunnels:
            for option_string in self.tunnels[thread_type]:
                (thread,queue,server,server_port) = self.tunnels[thread_type][option_string]
                self.__shutdown_thread__(thread,queue,server)

    def exit(self):
        '''
        Kill the current session if connected.
        '''
        if self.past_login==True:
            self.__shutdown_all__.set()
            self.close_tunnels()
            self.close_tunnels()
            if self.__check_for_attr__('sftp')==True:
                del self.sftp
            if self.__check_for_attr__('scp')==True:
                del self.scp
            if not self._ssh_keepalive_thread==None:
                self.__shutdown_thread__(self._ssh_keepalive_thread,self._ssh_keepalive_event,None)
            try:
                self._block(self.channel.close)
                self._block(self.session.disconnect)
            except:
                pass
            self.sock.close()
            del self.channel,self._ssh_keepalive_thread
            del self.session
            del self.sock
            self._ssh_keepalive_thread = None
            self._ssh_keepalive_event = None
            self.__shutdown_all__.clear()
            self.tunnels = {
                enums.TunnelType.local:{},
                enums.TunnelType.remote:{},
                enums.TunnelType.dynamic:{},
                enums.TunnelType.x11:{}
            }
            self.past_login = False
