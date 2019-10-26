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
from redssh import tunnelling


class RedSSH(object):
    '''
    Instances the start of an SSH connection.
    Extra options are available after :func:`redssh.RedSSH.connect` is called.

    :param encoding: Set the encoding to something other than the default of ``'utf8'`` when your target SSH server doesn't return UTF-8.
    :type encoding: ``str``
    :param terminal: Set the terminal sent to the remote server to something other than the default of ``'vt100'``.
    :type terminal: ``str``
    :param ssh_wait_time_window: Set the wait time between trying to retreive data from the remote server, changing this from the default value of ``0.01`` will turn off the auto detection method that is done at the time of the initial SSH handshake. Additionally this needs to be slightly larger than the ping time between the client and the server otherwise you will run into problems with the returned data.
    :type ssh_wait_time_window: ``float``
    :param ssh_host_key_verification: Change the behaviour of remote host key verification. Can be set to one of the following values, ``strict``, ``warn``, ``auto_add`` or ``none``.
    :type ssh_host_key_verification: :class:`redssh.enums.SSHHostKeyVerify`
    :param ssh_keepalive_interval: Enable or disable SSH keepalive packets, value is interval in seconds.
    :type ssh_keepalive_interval: ``float``
    '''
    def __init__(self,encoding='utf8',terminal='vt100',known_hosts=None,ssh_wait_time_window=None,
        ssh_host_key_verification=enums.SSHHostKeyVerify.warn,ssh_keepalive_interval=0.0):
        self.debug = False
        self._block_select_lock = multiprocessing.Lock()
        self.encoding = encoding
        self.tunnels = {'local':{},'remote':{}}
        self.terminal = terminal
        self.ssh_wait_time_window = ssh_wait_time_window
        self.ssh_wait_time_window_floor = 0.05
        self.ssh_host_key_verification = ssh_host_key_verification
        self.ssh_keepalive_interval = ssh_keepalive_interval
        self._ssh_keepalive_thread = None
        self._ssh_keepalive_event = None
        if known_hosts==None:
            self.known_hosts_path = os.path.join(os.path.expanduser('~'),'.ssh','known_hosts')
        else:
            self.known_hosts_path = known_hosts

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


    def _block_select(self,timeout=None):
        block_direction = self.session.block_directions()
        if block_direction==0:
            return(None)
        self._block_select_lock.acquire()
        rfds = []
        wfds = []
        if block_direction & libssh2.LIBSSH2_SESSION_BLOCK_INBOUND:
            rfds = [self.sock]
        if block_direction & libssh2.LIBSSH2_SESSION_BLOCK_OUTBOUND:
            wfds = [self.sock]
        select.select(rfds,wfds,[],timeout)
        self._block_select_lock.release()

    def _block(self,func,*args,**kwargs):
        out = func(*args,**kwargs)
        while out==libssh2.LIBSSH2_ERROR_EAGAIN:
            self._block_select()
            out = func(*args,**kwargs)
        return(out)

    def _block_write(self,func,data,timeout=None):
        data_len = len(data)
        total_written = 0
        while total_written<data_len:
            (rc,bytes_written) = func(data[total_written:])
            total_written+=bytes_written
            if rc==libssh2.LIBSSH2_ERROR_EAGAIN:
                self._block_select(timeout)

    def _read_iter(self,func,timeout=None):
        pos = 0
        remainder_len = 0
        remainder = b''
        (size,data) = func()
        while size==libssh2.LIBSSH2_ERROR_EAGAIN or size>0:
            if size==libssh2.LIBSSH2_ERROR_EAGAIN:
                self._block_select(timeout)
                (size,data) = func()
            if timeout is not None and size==libssh2.LIBSSH2_ERROR_EAGAIN:
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

    def check_host_key(self,hostname,port):
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

        if self.ssh_host_key_verification==enums.SSHHostKeyVerify.none:
            return(None)

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

    def connect(self,hostname,port=22,username=None,password=None,allow_agent=True,
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
        :param key_filepath: Array of filenames to offer to the remote server. Can be a string
        :type key_filepath: ``array``
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
                ping_timer = time.time()
                self.sock = socket.create_connection((hostname,port),timeout)
                ping_timer = float(time.time()-ping_timer)
                if self.ssh_wait_time_window==None:
                    self.ssh_wait_time_window = ping_timer
                self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
            else:
                self.sock = sock
            self.session = libssh2.Session()
            # self.session.publickey_init()
            ping_timer = time.time()
            self.session.handshake(self.sock)
            ping_timer = float(time.time()-ping_timer)/3.2
            if self.ssh_wait_time_window==None:
                self.ssh_wait_time_window = ping_timer
            if self.ssh_wait_time_window<self.ssh_wait_time_window_floor:
                self.ssh_wait_time_window = self.ssh_wait_time_window_floor
            # print(self.ssh_wait_time_window)

            self.check_host_key(hostname,port)

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
                self.session.keepalive_config(False, self.ssh_keepalive_interval)
                self._ssh_keepalive_thread = threading.Thread(target=self.ssh_keepalive)
                self._ssh_keepalive_event = threading.Event()
                self._ssh_keepalive_thread.start()
            self.channel = self._block(self.session.open_session)
            self._block(self.channel.pty,self.terminal)
            self._block(self.channel.shell)
            self.past_login = True
            self.device_init()


    def device_init(self,**kwargs):
        '''
        Override this function to intialize a device that does not simply drop to the terminal or a device will kick you out if you send any key/character other than an "acceptable" one.
        This default one will work on linux quite well but devices such as pfsense or mikrotik might require this function and :func:`redexpect.RedExpect.get_unique_prompt` to be overriden.
        '''
        pass


    def read(self,wait_time=None):
        '''
        Recieve data from the remote session.
        Only works if the current session has made it past the login process.

        :param wait_time: Block for this long to recieve data from the remote session.
        :type wait_time: ``float``
        :return: ``generator`` - A generator of byte strings that has been recieved in the time given.
        '''
        if wait_time==None:
            wait_time = self.ssh_wait_time_window
        if self.past_login==True:
            return(self._read_iter(self.channel.read,wait_time))

    def send(self,string):
        '''
        Send data to the remote session.
        Only works if the current session has made it past the login process.

        :param string: String to send to the remote session.
        :type string: ``str``
        '''
        if self.past_login==True:
            self._block_write(self.channel.write,string)

    def last_error(self):
        '''
        Get the last error from the current session.

        :return: ``str``
        '''
        return(self._block(self.session.last_error))

    def start_sftp(self):
        '''
        Start the SFTP client.
        '''
        if self.__check_for_attr__('past_login') and self.__check_for_attr__('sftp')==False:
            self.sftp = sftp.RedSFTP(self)

    def local_tunnel(self,local_port,remote_host,remote_port,bind_addr=''):
        '''

        Forwards a port the same way the ``-L`` option does for the OpenSSH client.

        :param local_port: The local port on the local machine to connect to.
        :type local_port: ``int``
        :param remote_host: The remote host to connect to via the remote machine.
        :type remote_host: ``str``
        :param remote_port: The remote host's port to connect to via the remote machine.
        :type remote_port: ``int``
        :param bind_addr: The bind address on this machine to bind to for the local port.
        :type bind_addr: ``str``
        :return: ``tuple`` of ``(tun_thread,thread_terminate,tun_server,tun_server_port)`` this is so you can control the tunnel's thread if you need to.
        '''
        option_string = str(local_port)+':'+remote_host+':'+str(remote_port)
        if not option_string in self.tunnels['local']:
            wait_for_chan = threading.Event()
            thread_terminate = threading.Event()

            class SubHander(tunnelling.LocalPortHandler):
                caller = self
                chain_host = remote_host
                chain_port = remote_port
                terminate = thread_terminate
                wchan = wait_for_chan

            tun_server = tunnelling.LocalPortServer((bind_addr,local_port),SubHander,self,remote_host,remote_port,wait_for_chan)
            tun_thread = threading.Thread(target=tun_server.serve_forever)
            tun_thread.daemon = True
            tun_thread.name = 'local:'+option_string
            tun_thread.start()
            wait_for_chan.wait()
            if local_port==0:
                local_port = tun_server.socket.getsockname()[1]
                option_string = str(local_port)+':'+remote_host+':'+str(remote_port)
            self.tunnels['local'][option_string] = (tun_thread,thread_terminate,tun_server,local_port)
        return(self.tunnels['local'][option_string])

    def remote_tunnel(self,local_port,remote_host,remote_port,bind_addr=''):
        '''

        Forwards a port the same way the ``-R`` option does for the OpenSSH client.

        :param local_port: The local port on the remote side to connect to.
        :type local_port: ``int``
        :param remote_host: The remote host to connect to via the local machine.
        :type remote_host: ``str``
        :param remote_port: The remote host's port to connect to via the local machine.
        :type remote_port: ``int``
        :return: ``tuple`` of ``(tun_thread,thread_terminate,None,None)`` this is so you can control the tunnel's thread if you need to.
        '''
        option_string = str(local_port)+':'+remote_host+':'+str(remote_port)
        if not option_string in self.tunnels['remote']:
            wait_for_chan = threading.Event()
            thread_terminate = threading.Event()
            tun_thread = threading.Thread(target=tunnelling.remote_handler,args=(self,remote_host,remote_port,bind_addr,local_port,thread_terminate,wait_for_chan))
            tun_thread.daemon = True
            tun_thread.name = 'remote:'+option_string
            tun_thread.start()
            wait_for_chan.wait()
            self.tunnels['remote'][option_string] = (tun_thread,thread_terminate,None,None)
        return(self.tunnels['remote'][option_string])


    def close_tunnels(self):
        '''
        Closes all SSH tunnels if any are open.
        '''
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
                if self.__check_for_attr__('sftp')==True:
                    del self.sftp
                self.close_tunnels()
                if not self._ssh_keepalive_thread==None:
                    self.__shutdown_thread__(self._ssh_keepalive_thread,self._ssh_keepalive_event,None)
                self._block(self.channel.close)
                self._block(self.session.disconnect)
                self.sock.close()
                del self.sock,self.session,self.channel,self.past_login,self._ssh_keepalive_thread
                # ssh2.utils.ssh2_exit()
