# RedSSH
# Copyright (C) 2019  Red_M ( http://bitbucket.com/Red_M )

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
import time
import hashlib
import threading
import multiprocessing
import socket
import select
import ssh2

from redssh import libssh2
from redssh import exceptions
from redssh import enums
from redssh import sftp
from redssh import scp
from redssh import tunnelling


class RedSSH(object):
    '''
    Instances the start of an SSH connection.
    Extra options are available after :func:`redssh.RedSSH.connect` is called.

    :param encoding: Set the encoding to something other than the default of ``'utf8'`` when your target SSH server doesn't return UTF-8.
    :type encoding: ``str``
    :param terminal: Set the terminal sent to the remote server to something other than the default of ``'vt100'``.
    :type terminal: ``str``
    :param ssh_host_key_verification: Change the behaviour of remote host key verification. Can be set to one of the following values, ``strict``, ``warn``, ``auto_add`` or ``none``.
    :type ssh_host_key_verification: :class:`redssh.enums.SSHHostKeyVerify`
    :param ssh_keepalive_interval: Enable or disable SSH keepalive packets, value is interval in seconds.
    :type ssh_keepalive_interval: ``float``
    :param set_flags: Not supported in ssh2-python 0.18.0
    :type set_flags: ``dict``
    :param method_preferences: Not supported in ssh2-python 0.18.0
    :type method_preferences: ``dict``
    '''
    def __init__(self,encoding='utf8',terminal='vt100',known_hosts=None,ssh_host_key_verification=enums.SSHHostKeyVerify.warn,
        ssh_keepalive_interval=0.0,set_flags={},method_preferences={}):
        self.debug = False
        self._block_lock = multiprocessing.RLock()
        self.__shutdown_all__ = multiprocessing.Event()
        self.encoding = encoding
        self.tunnels = {enums.TunnelType.local.value:{},enums.TunnelType.remote.value:{},enums.TunnelType.dynamic.value:{}}
        self.terminal = terminal
        self.ssh_host_key_verification = ssh_host_key_verification
        self.ssh_keepalive_interval = ssh_keepalive_interval
        self.request_pty = True
        self.set_flags = set_flags
        self.method_preferences = method_preferences
        self._ssh_keepalive_thread = None
        self._ssh_keepalive_event = None
        if known_hosts==None:
            self.known_hosts_path = os.path.join(os.path.expanduser('~'),'.ssh','known_hosts')
        else:
            self.known_hosts_path = known_hosts

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

    def ssh_keepalive(self):
        timeout = 0.01
        while self.__check_for_attr__('channel')==False:
            time.sleep(timeout)
        while self._ssh_keepalive_event.is_set()==False and self.__check_for_attr__('channel')==True:
            timeout = self._block(self.session.keepalive_send)
            self._ssh_keepalive_event.wait(timeout=timeout)


    def _block_select(self):
        with self._block_lock:
            block_direction = self.session.block_directions()
            if block_direction==0:
                return(None)
            rfds = []
            wfds = []
            if block_direction & libssh2.LIBSSH2_SESSION_BLOCK_INBOUND:
                rfds = [self.sock]
            if block_direction & libssh2.LIBSSH2_SESSION_BLOCK_OUTBOUND:
                wfds = [self.sock]
            select.select(rfds,wfds,[],0.001)

    def _block(self,func,*args,**kwargs):
        if self.__shutdown_all__.is_set()==False:
            with self._block_lock:
                out = func(*args,**kwargs)
            while out==libssh2.LIBSSH2_ERROR_EAGAIN:
                self._block_select()
                with self._block_lock:
                    out = func(*args,**kwargs)
            return(out)

    def _block_write(self,func,data):
        data_len = len(data)
        total_written = 0
        while total_written<data_len:
            if self.__shutdown_all__.is_set()==False:
                with self._block_lock:
                    (rc,bytes_written) = func(data[total_written:])
                total_written+=bytes_written
                if rc==libssh2.LIBSSH2_ERROR_EAGAIN:
                    self._block_select()
        return(total_written)

    def _read_iter(self,func,block=False):
        pos = 0
        remainder_len = 0
        remainder = b''
        if self.__shutdown_all__.is_set()==False:
            with self._block_lock:
                (size,data) = func()
            while size==libssh2.LIBSSH2_ERROR_EAGAIN or size>0:
                if size==libssh2.LIBSSH2_ERROR_EAGAIN:
                    self._block_select()
                    if self.__shutdown_all__.is_set()==False:
                        with self._block_lock:
                            (size,data) = func()
                # if timeout is not None and size==libssh2.LIBSSH2_ERROR_EAGAIN:
                if size==libssh2.LIBSSH2_ERROR_EAGAIN and block==False:
                    return(b'')
                while size>0:
                    while pos<size:
                        if remainder_len>0:
                            yield(remainder+data[pos:size])
                            remainder = b''
                            remainder_len = 0
                        else:
                            yield(data[pos:size])
                        pos = size
                    self._block_select()
                    with self._block_lock:
                        (size,data) = func()
                    pos = 0
            if remainder_len>0:
                yield(remainder)

    def eof(self):
        '''
        Returns ``True`` or ``False`` when the main channel has recieved an ``EOF``.
        '''
        if self.__check_for_attr__('channel')==True:
            return(self._block(self.channel.eof))

    def methods(self, method):
        '''
        Returns what value was settled on during session negotiation.
        '''
        if self.__check_for_attr__('session')==True:
            if 'methods' in dir(self.session): # remove once my fork is merged.
                return(self._block(self.session.methods,method))

    def supported_algs(self, method, algs):
        '''
        Returns what values are available for session negotiation.
        '''
        if self.__check_for_attr__('session')==True:
            if 'supported_algs' in dir(self.session): # remove once my fork is merged.
                return(self._block(self.session.supported_algs,method,algs))

    def setenv(self, varname, value):
        '''
        Set an environment variable on the channel.

        :param varname: Name of environment variable to set on the remote channel.
        :type varname: ``str``
        :param value: Value to set ``varname`` to.
        :type value: ``str``
        :return: ``None``
        '''
        if self.__check_for_attr__('past_login'):
            self._block(self.channel.setenv,varname,value)

    def check_host_key(self,hostname,port):
        if self.ssh_host_key_verification==enums.SSHHostKeyVerify.none:
            return(None)

        self.known_hosts = self.session.knownhost_init()
        if os.path.exists(self.known_hosts_path)==True:
            self.known_hosts.readfile(self.known_hosts_path)
        (host_key,host_key_type) = self.session.hostkey()

        if isinstance(hostname,type('')):
            hostname = hostname.encode(self.encoding)
        if host_key_type==libssh2.LIBSSH2_HOSTKEY_TYPE_RSA:
            server_key_type = libssh2.LIBSSH2_KNOWNHOST_KEY_SSHRSA
        else:
            server_key_type = libssh2.LIBSSH2_KNOWNHOST_KEY_SSHDSS
        key_bitmask = libssh2.LIBSSH2_KNOWNHOST_TYPE_PLAIN|libssh2.LIBSSH2_KNOWNHOST_KEYENC_RAW|server_key_type


        if self.ssh_host_key_verification==enums.SSHHostKeyVerify.strict:
            self.known_hosts.checkp(hostname,port,host_key,key_bitmask)

        if self.ssh_host_key_verification==enums.SSHHostKeyVerify.warn:
            try:
                self.known_hosts.checkp(hostname,port,host_key,key_bitmask)
            except Exception as e:
                print('WARN: '+str(e))

        if self.ssh_host_key_verification in [enums.SSHHostKeyVerify.auto_add,enums.SSHHostKeyVerify.warn_auto_add]:
            try:
                self.known_hosts.checkp(hostname,port,host_key,key_bitmask)
                return(None)
            except Exception as e:
                if self.ssh_host_key_verification==enums.SSHHostKeyVerify.warn_auto_add:
                    print('WARN: '+str(e))
            self.known_hosts.addc(hostname,host_key,key_bitmask)
            self.known_hosts.writefile(self.known_hosts_path)

    def connect(self,hostname,port=22,username=None,password=None,allow_agent=False,
        #host_based=None,
        key_filepath=None,passphrase=None,look_for_keys=True,sock=None,timeout=None):
        '''
        .. warning::
            Some authentication methods are not yet supported!

        :param hostname: Hostname to connect to.
        :type hostname: ``str``
        :param port: SSH port to connect to.
        :type port: ``int``
        :param username: Username to connect as to the remote server.
        :type username: ``str``
        :param password: Password to offer to the remote server for authentication.
        :type password: ``str``
        :param allow_agent: Allow the local SSH key agent to offer the keys held in it for authentication.
        :type allow_agent: ``bool``
        :param key_filepath: Array of filenames to offer to the remote server. Can be a string for a single key.
        :type key_filepath: ``array``/``str``
        :param passphrase: Passphrase to decrypt any keys offered to the remote server.
        :type passphrase: ``str``
        :param look_for_keys: Enable offering keys in ``~/.ssh`` automatically. NOT IMPLEMENTED!
        :type look_for_keys: ``bool``
        :param sock: A pre-connected socket to the remote server. Useful if you have strange network requirements.
        :type sock: ``socket``
        :param timeout: Timeout for the socket connection to the remote server.
        :type timeout: ``float``
        '''
        if self.__check_for_attr__('past_login')==False:
            if sock==None:
                self.sock = socket.create_connection((hostname,port),timeout)
                self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
            else:
                self.sock = sock
            self.session = libssh2.Session()
            # self.session.publickey_init()

            if 'flag' in dir(self.session): # remove once my fork is merged.
                if not self.set_flags=={}:
                    for flag in self.set_flags:
                        self.session.flag(flag, self.set_flags[flag])

            if 'method_pref' in dir(self.session): # remove once my fork is merged.
                if not self.method_preferences=={}:
                    for pref in self.method_preferences:
                        self.session.method_pref(pref, self.method_preferences[pref])

            self.session.handshake(self.sock)

            self.check_host_key(hostname,port) # segfault on real ssh server????

            auth_requests = self.session.userauth_list(username)
            authenticated = False
            auth_types_tried = []
            for auth_request in auth_requests:
                if auth_request=='publickey':
                    if allow_agent==True:
                        auth_types_tried.append('publickey')
                        try:
                            self.session.agent_auth(username)
                            if self.session.userauth_authenticated()==True:
                                authenticated = True
                                break
                        except:
                            pass
                    elif not key_filepath==None:
                        if isinstance(key_filepath,type(''))==True:
                            key_filepath = [key_filepath]
                        if isinstance(key_filepath,type([]))==True:
                            if passphrase==None:
                                passphrase = ''
                            for private_key in key_filepath:
                                if os.path.exists(private_key) and os.path.isfile(private_key):
                                    auth_types_tried.append('publickey')
                                    try:
                                        self.session.userauth_publickey_fromfile(username,private_key,passphrase)
                                        if self.session.userauth_authenticated()==True:
                                            authenticated = True
                                            break
                                    except:
                                        pass
                    # elif host_based==True:
                        # auth_types_tried.append('hostbased')
                        # try:
                            # self.session.userauth_hostbased_fromfile(username,private_key,hostname,passphrase=passphrase)
                            # if self.session.userauth_authenticated()==True:
                                # authenticated = True
                                # break
                        # except:
                            # pass
                if not password==None:
                    if auth_request=='password':
                        auth_types_tried.append('password')
                        try:
                            self.session.userauth_password(username,password)
                            if self.session.userauth_authenticated()==True:
                                authenticated = True
                                break
                        except:
                            pass
                    if auth_request=='keyboard-interactive':
                        auth_types_tried.append('keyboard-interactive') # not implemented in ssh2-python 0.18.0
                        # bugged in ssh2-python's implementation for 1.9.0 of libssh2
                        # but fixed in my fork. :)
                        try:
                            self.session.userauth_keyboardinteractive(username,password)
                            if self.session.userauth_authenticated()==True:
                                authenticated = True
                                break
                        except:
                            pass
            if authenticated==False:
                raise(exceptions.AuthenticationFailedException(list(set(auth_types_tried))))

            self.session.set_blocking(False)
            if not self.ssh_keepalive_interval==0:
                self.session.keepalive_config(True, self.ssh_keepalive_interval)
                self._ssh_keepalive_thread = threading.Thread(target=self.ssh_keepalive)
                self._ssh_keepalive_event = threading.Event()
                self._ssh_keepalive_thread.start()
            self.channel = self._block(self.session.open_session)
            if self.request_pty==True:
                self._block(self.channel.pty,self.terminal)
            self._block(self.channel.shell)
            self.past_login = True

    def read(self,block=False):
        '''
        Recieve data from the remote session.
        Only works if the current session has made it past the login process.

        :param block: Block until data is received from the remote server. ``True``
        will block until data is recieved and ``False`` may return ``b''`` if no data is available from the remote server.
        :type block: ``bool``
        :return: ``generator`` - A generator of byte strings that has been recieved in the time given.
        '''
        if self.__check_for_attr__('past_login')==True:
            if self.past_login==True:
                return(self._read_iter(self.channel.read,block))
        return([])

    def send(self,string):
        '''
        Send data to the remote session.
        Only works if the current session has made it past the login process.

        :param string: String to send to the remote session.
        :type string: ``str``
        :return: ``int`` - Amount of bytes sent to remote machine.
        '''
        if self.__check_for_attr__('past_login')==True:
            if self.past_login==True:
                return(self._block_write(self.channel.write,string))
        return(0)

    def last_error(self):
        '''
        Get the last error from the current session.

        :return: ``str``
        '''
        return(self._block(self.session.last_error))

    def start_sftp(self):
        '''
        Start the SFTP client.

        :return: ``None``
        '''
        if self.__check_for_attr__('past_login') and self.__check_for_attr__('sftp')==False:
            self.sftp = sftp.RedSFTP(self)

    def start_scp(self):
        '''
        Start the SCP client.

        :return: ``None``
        '''
        if self.__check_for_attr__('past_login') and self.__check_for_attr__('scp')==False:
            self.scp = scp.RedSCP(self)


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
        :type error_level: ``redssh.enums.TunnelErrorLevel``
        :return: ``int`` The local port that has been bound.
        '''
        assert isinstance(remote_host,type(''))
        assert isinstance(remote_port,type(0))
        option_string = str(bind_addr)+':'+str(local_port)+':'+remote_host+':'+str(remote_port)
        if not option_string in self.tunnels[enums.TunnelType.local.value]:
            wait_for_chan = threading.Event()
            thread_terminate = threading.Event()

            class SubHander(tunnelling.LocalPortServerHandler):
                caller = self
                chain_host = remote_host
                chain_port = remote_port
                terminate = thread_terminate
                wchan = wait_for_chan

            tun_server = tunnelling.LocalPortServer((bind_addr,local_port),SubHander,self,remote_host,remote_port,wait_for_chan,error_level)
            tun_thread = threading.Thread(target=tun_server.serve_forever)
            tun_thread.daemon = True
            tun_thread.name = enums.TunnelType.local.value+':'+option_string
            tun_thread.start()
            wait_for_chan.wait()
            if local_port==0:
                local_port = tun_server.socket.getsockname()[1]
                option_string = str(local_port)+':'+remote_host+':'+str(remote_port)
                tun_thread.name = enums.TunnelType.local.value+':'+option_string
            self.tunnels[enums.TunnelType.local.value][option_string] = (tun_thread,thread_terminate,tun_server,local_port)
        return(local_port)

    def remote_tunnel(self,local_port,remote_host,remote_port,bind_addr='127.0.0.1',error_level=enums.TunnelErrorLevel.warn):
        '''

        Forwards a port to the remote machine via the local machine the same way the ``-R`` option does for the OpenSSH client.

        :param local_port: The local port on the remote side to connect to.
        :type local_port: ``int``
        :param remote_host: The remote host to connect to via the local machine.
        :type remote_host: ``str``
        :param remote_port: The remote host's port to connect to via the local machine.
        :type remote_port: ``int``
        :param error_level: The level of verbosity that errors in tunnel threads will use.
        :type error_level: ``redssh.enums.TunnelErrorLevel``
        :return: ``None``
        '''
        option_string = str(bind_addr)+':'+str(local_port)+':'+remote_host+':'+str(remote_port)
        if not option_string in self.tunnels[enums.TunnelType.remote.value]:
            wait_for_chan = threading.Event()
            thread_terminate = threading.Event()
            tun_thread = threading.Thread(target=tunnelling.remote_tunnel_server,args=(self,remote_host,remote_port,bind_addr,local_port,thread_terminate,wait_for_chan,error_level))
            tun_thread.daemon = True
            tun_thread.name = enums.TunnelType.remote.value+':'+option_string
            tun_thread.start()
            wait_for_chan.wait()
            self.tunnels[enums.TunnelType.remote.value][option_string] = (tun_thread,thread_terminate,None,None)
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
        :type error_level: ``redssh.enums.TunnelErrorLevel``
        :return: ``int`` The local port that has been bound.
        '''
        option_string = bind_addr+':'+str(local_port)
        if not option_string in self.tunnels[enums.TunnelType.dynamic.value]:
            wait_for_chan = threading.Event()
            thread_terminate = threading.Event()

            class SubHander(tunnelling.LocalPortServerHandler):
                caller = self
                chain_host = None
                chain_port = None
                terminate = thread_terminate
                wchan = wait_for_chan

            tun_server = tunnelling.LocalPortServer((bind_addr,local_port),SubHander,self,None,None,wait_for_chan,error_level)
            tun_thread = threading.Thread(target=tun_server.serve_forever)
            tun_thread.daemon = True
            tun_thread.name = enums.TunnelType.dynamic.value+':'+option_string
            tun_thread.start()
            wait_for_chan.wait()
            if local_port==0:
                local_port = tun_server.socket.getsockname()[1]
                option_string = str(local_port)
                tun_thread.name = enums.TunnelType.dynamic.value+':'+option_string
            self.tunnels[enums.TunnelType.dynamic.value][option_string] = (tun_thread,thread_terminate,tun_server,local_port)
        return(local_port)

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
        :type tunnel_type: ``redssh.enums.TunnelType``
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
            if option_string in self.tunnels[tunnel_type.value]:
                (thread,queue,server,server_port) = self.tunnels[tunnel_type.value][option_string]
                self.__shutdown_thread__(thread,queue,server)
                del self.tunnels[tunnel_type.value][option_string]


    def close_tunnels(self):
        '''
        Closes all SSH tunnels if any are open.
        '''
        if self.__check_for_attr__('tunnels')==True:
            for thread_type in self.tunnels:
                for option_string in self.tunnels[thread_type]:
                    (thread,queue,server,server_port) = self.tunnels[thread_type][option_string]
                    self.__shutdown_thread__(thread,queue,server)
            del self.tunnels

    def exit(self):
        '''
        Kill the current session if actually connected.
        After this you might as well just free memory from the class instance.
        '''
        if self.__check_for_attr__('past_login')==True:
            if self.past_login==True:
                self.__shutdown_all__.set()
                if self.__check_for_attr__('sftp')==True:
                    del self.sftp
                self.close_tunnels()
                if not self._ssh_keepalive_thread==None:
                    self.__shutdown_thread__(self._ssh_keepalive_thread,self._ssh_keepalive_event,None)
                try:
                    self._block(self.channel.close)
                    self._block(self.session.disconnect)
                except:
                    pass
                self.sock.close()
                del self.channel,self.past_login,self._ssh_keepalive_thread
                del self.session
                del self.sock
