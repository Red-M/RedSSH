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
import time
import hashlib
import threading
import multiprocessing
import socket
import select

from redssh.clients.baseclient import BaseClient, BaseClientModules
from redssh.clients.libssh import libssh
from redssh import exceptions
from redssh import enums
from redssh.clients.libssh import sftp
from redssh.clients.libssh import scp
from redssh.clients.libssh import tunneling
from redssh.clients.libssh import x11

class LibSSHModules(BaseClientModules):
    scp = scp
    sftp = sftp
    tunneling = tunneling
    x11 = x11

class LibSSH(BaseClient):
    '''
    Instances the start of an SSH connection.
    Extra options are available after :func:`redssh.RedSSH.connect` is called.
    Older versions of Pageant will not authenticate correctly with this client, please update your agent!

    :param encoding: Set the encoding to something other than the default of ``'utf8'`` when your target SSH server doesn't return UTF-8.
    :type encoding: ``str``
    :param terminal: Set the terminal sent to the remote server to something other than the default of ``'vt100'``.
    :type terminal: ``str``
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
    def __init__(self,*args,set_flags={},method_preferences={},callbacks={},**kwargs):
        super().__init__(*args,**kwargs)

        self.session = libssh.Session()
        self.set_flags = set_flags
        self.method_preferences = method_preferences
        self.callbacks = callbacks
        self._ssh_keepalive_thread = None
        self._ssh_keepalive_event = None
        self._modules = LibSSHModules

    def ssh_keepalive(self):
        timeout = 0.01
        while self.__check_for_attr__('channel')==False:
            time.sleep(timeout)
        while self._ssh_keepalive_event.is_set()==False and self.__check_for_attr__('channel')==True:
            timeout = self._block(self.session.keepalive_send,_select_timeout=self._select_timeout)
            self._ssh_keepalive_event.wait(timeout=timeout)

    def _block(self,func,*args,**kwargs):
        if self.__shutdown_all__.is_set()==False:
            default_str = 'sdkljfhklsdjf'
            _select_timeout = kwargs.get('_select_timeout',default_str)
            if _select_timeout==default_str:
                _select_timeout = None
            else:
                _select_timeout = float(_select_timeout)
                del kwargs['_select_timeout']
            out = libssh.error_codes.SSH_AGAIN
            while out==libssh.error_codes.SSH_AGAIN:
                self._block_select(_select_timeout)
                with self.session._block_lock:
                    out = func(*args,**kwargs)
            return(out)

    def _block_write(self,func,data,_select_timeout=None):
        data_len = len(data)
        total_written = 0
        while total_written<data_len:
            if self.__shutdown_all__.is_set()==False:
                with self.session._block_lock:
                    (rc,bytes_written) = func(data[total_written:])
                total_written+=bytes_written
                if rc==libssh.error_codes.SSH_AGAIN:
                    self._block_select(_select_timeout)
        return(total_written)

    def _read_iter(self,func,block=False,max_read=-1,_select_timeout=None):
        pos = 0
        remainder_len = 0
        remainder = b''
        if self.__shutdown_all__.is_set()==False:
            with self.session._block_lock:
                (size,data) = func()
            while size==libssh.error_codes.SSH_AGAIN or size>0:
                if size==libssh.error_codes.SSH_AGAIN:
                    self._block_select(_select_timeout)
                    if self.__shutdown_all__.is_set()==False:
                        with self.session._block_lock:
                            (size,data) = func()
                # if timeout is not None and size==libssh.error_codes.SSH_AGAIN:
                if size==libssh.error_codes.SSH_AGAIN and (block==False or (max_read>size and max_read!=-1)):
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
                    self._block_select(_select_timeout)
                    with self.session._block_lock:
                        try:
                            (size,data) = func()
                        except libssh.exceptions.EOF:
                            return(b'')
                    pos = 0
            if remainder_len>0:
                yield(remainder)

    def _auth(self,username,password,allow_agent,host_based,key_filepath,passphrase,look_for_keys):
        auth_supported = self._auth_get_supported()
        auth_types_tried = []
        if isinstance(auth_supported,type([])):

            if libssh.enums.Auth_Method.PUBLICKEY in auth_supported:
                if allow_agent==True:
                    auth_types_tried.append('publickey')
                    if self._auth_attempt(self.session.userauth_agent)==libssh.SSH_AUTH_SUCCESS:
                        return()
                elif key_filepath!=None:
                    auth_types_tried.append('publickey')
                    pkey = libssh.key.import_privkey_file(key_filepath,passphrase)
                    if self._auth_attempt(self.session.userauth_publickey,pkey)==libssh.SSH_AUTH_SUCCESS:
                        return()

                # elif host_based==True:
                    # auth_types_tried.append('hostbased')
                    # if res==self._auth_attempt(self.session.userauth_hostbased_fromfile,username,private_key,hostname,passphrase=passphrase):
                        # return()
            if not password==None:
                if libssh.enums.Auth_Method.PASSWORD in auth_supported:
                    auth_types_tried.append('password')
                    if self._auth_attempt(self.session.userauth_password,None,password)==libssh.SSH_AUTH_SUCCESS:
                        return()
                # if libssh.enums.Auth_Method.INTERACTIVE in auth_supported:
                    # auth_types_tried.append('keyboard-interactive')
                    # if self._auth_attempt(self.session.userauth_keyboardinteractive,None,password)==libssh.SSH_AUTH_SUCCESS:
                        # return()

        raise(exceptions.AuthenticationFailedException(list(set(auth_types_tried))))

    def _auth_get_supported(self):
        try:
            self.session.userauth_none()
        except Exception as e:
            pass
        server_auth_supported = self.session.userauth_list()
        auth_supported = []
        for auth_meth in libssh.enums.Auth_Method:
            if (server_auth_supported & auth_meth.value)>0:
                auth_supported.append(auth_meth)
        return(auth_supported)

    def _auth_attempt(self,func,*args,**kwargs):
        try:
            return(func(*args,**kwargs))
        except Exception as e:
            pass

    def eof(self):
        '''
        Returns ``True`` or ``False`` when the main channel has recieved an ``EOF``.
        '''
        if self.__check_for_attr__('channel')==True:
            return(self._block(self.channel.is_eof))

    def methods(self, method):
        pass
        # '''
        # Returns what value was settled on during session negotiation.
        # '''
        # if self.__check_for_attr__('session')==True:
            # return(self._block(self.session.methods,method))

    def setenv(self, varname, value):
        '''
        Set an environment variable on the mainchannel.

        :param varname: Name of environment variable to set on the remote channel.
        :type varname: ``str``
        :param value: Value to set ``varname`` to.
        :type value: ``str``
        :return: ``None``
        '''
        if self.past_login==True:
            self._block(self.channel.request_env,varname,value)

    def check_host_key(self): # TODO, properly get this working
        if self.ssh_host_key_verification==enums.SSHHostKeyVerify.none:
            return(None)
        server_known = self.session.is_server_known()
        if server_known==False:
            pass

    def connect(self,hostname,port=22,username='',password=None,
        allow_agent=False,host_based=None,key_filepath=None,passphrase=None,
        look_for_keys=False,sock=None,timeout=None):
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
        :param host_based: Allow the local SSH host keys to be used for authentication. NOT IMPLEMENTED!
        :type host_based: ``bool``
        :param key_filepath: Array of filenames to offer to the remote server. Can be a string for a single key.
        :type key_filepath: ``array``/``str``
        :param passphrase: Passphrase to decrypt any keys offered to the remote server.
        :type passphrase: ``str``
        :param look_for_keys: Enable offering keys in ``~/.ssh`` automatically. NOT IMPLEMENTED!
        :type look_for_keys: ``bool``
        :param sock: A pre-connected socket to the remote server. Useful if you have strange network requirements.
        :type sock: :func:`socket.socket`
        :param timeout: Timeout for the socket connection to the remote server.
        :type timeout: ``float``
        '''
        if password==None and allow_agent==False and host_based==None and key_filepath==None and look_for_keys==False:
            raise(exceptions.NoAuthenticationOfferedException())
        if self.past_login==False:
            if sock==None:
                self.sock = socket.create_connection((hostname,port),timeout)
                self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
                self.sock.setsockopt(socket.IPPROTO_TCP,socket.TCP_NODELAY,self.tcp_nodelay)
            else:
                self.sock = sock
            # self.session.publickey_init()

            if not self.set_flags=={}:
                for flag in self.set_flags:
                    self.session.flag(flag, self.set_flags[flag])

            if not self.method_preferences=={}:
                for pref in self.method_preferences:
                    self.session.method_pref(pref, self.method_preferences[pref])

            # if 'callback_set' in dir(self.session):
                # if not self.callbacks=={}:
                    # for cbtype in self.callbacks:
                        # self.session.callback_set(cbtype, self.callbacks[cbtype])

            self.session.options_set(libssh.options.HOST, hostname)
            self.session.options_set(libssh.options.USER, username)
            self.session.options_set_port(self.sock.getsockname()[1])
            self.session.set_socket(self.sock)
            self.session.connect()

            # __initial = time.time()
            # self.session.keepalive_send()
            # new_select_timeout = float(time.time()-__initial)
            # if new_select_timeout>self._select_timeout and self._auto_select_timeout_enabled==True:
                # self._select_timeout = new_select_timeout

            self.check_host_key()

            self._auth(username,password,allow_agent,host_based,key_filepath,passphrase,look_for_keys)

            # if self.ssh_keepalive_interval>0:
                # self.session.keepalive_config(True, self.ssh_keepalive_interval)
                # self._ssh_keepalive_thread = threading.Thread(target=self.ssh_keepalive)
                # self._ssh_keepalive_event = threading.Event()
                # self._ssh_keepalive_thread.start()
            self.session.set_blocking(False)
            self.channel = self.open_channel(True,True)

            # if 'callback_set' in dir(self.session):
                # self._forward_x11()

            self._block(self.channel.request_shell)
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
        if self.past_login==True:
            return(self._read_iter(self.channel.read_nonblocking,block))
        return([])

    def send(self,string):
        '''
        Send data to the remote session.
        Only works if the current session has made it past the login process.

        :param string: String to send to the remote session.
        :type string: ``str``
        :return: ``int`` - Amount of bytes sent to remote machine.
        '''
        if self.past_login==True:
            return(self._block_write(self.channel.write,string))
        return(0)

    def flush(self):
        '''
        Flush all data on the primary channel's stdin to the remote connection.
        Only works if connected, otherwise returns ``0``.

        :return: ``int`` - Amount of bytes sent to remote machine.
        '''
        if self.past_login==True:
            return(self._block(self.channel.flush))
        return(0)

    def last_error(self):
        '''
        Get the last error from the current session.

        :return: ``str``
        '''
        return(self._block(self.session.get_error))

    def open_channel(self,shell=True,pty=False):
        channel = self._block(self.session.channel_new)
        self._block(channel.set_blocking,False)
        if shell==True:
            self._block(channel.open_session)
        if self.request_pty==True and pty==True:
            self._block(channel.request_pty_size,self.terminal,0,0)
        return(channel)

    def execute_command(self,command,env=None):
        '''
        Run a command. This will block as the command executes.

        :param command: Command to execute.
        :type command: ``str``
        :param env: Environment variables to set during ``command``.
        :type env: ``dict``
        :return: ``tuple (int, str)`` - of ``(return_code, command_output)``
        '''
        if env==None:
            env = {}
        if len(env)>0:
            for key in env:
                self.setenv(key,env[key])
        out = b''
        channel = self.open_channel(True,True)
        self._block(channel.request_exec,command)
        ret = self._block(channel.get_exit_status)
        while self._block(channel.is_eof)==False and ret==-1:
            ret = self._block(channel.get_exit_status)
        iter = self._read_iter(channel.read_nonblocking,True)
        for data in iter:
            out+=data
        self._block(channel.send_eof)
        self._block(channel.close)
        del channel
        return(ret,out)

    def start_sftp(self):
        '''
        Start the SFTP client.
        The client will be available at `self.sftp` and will be an instance of `redssh.sftp.RedSFTP`

        :return: ``None``
        '''
        if self.past_login and self.__check_for_attr__('sftp')==False:
            self.sftp = sftp.RedSFTP(self)

    def start_scp(self):
        '''
        Start the SCP client.

        :return: ``None``
        '''
        if self.past_login and self.__check_for_attr__('scp')==False:
            self.scp = scp.RedSCP(self)


    # def _forward_x11(self):
        # if libssh2.LIBSSH2_CALLBACK_X11 in self.callbacks:
            # self.x11_channels = []
            # disp = 0
            # thread_terminate = threading.Event()
            # self._block(self.channel.x11_req, disp)
            # forward_thread = threading.Thread(target=x11.forward,args=(self,thread_terminate))
            # forward_thread.daemon = True
            # forward_thread.name = enums.TunnelType.x11.value+':'+str(disp)
            # forward_thread.start()
            # self.tunnels[enums.TunnelType.x11.value][disp] = (forward_thread,thread_terminate,None,None)
