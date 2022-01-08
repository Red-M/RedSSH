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
import socket

from . import exceptions
from . import enums
from . import clients


class RedSSH(object):
    '''
    Instances the start of an SSH connection.
    Extra options are available after :func:`redssh.RedSSH.connect` is called.

    :param encoding: Set the encoding to something other than the default of ``'utf8'`` when your target SSH server doesn't return UTF-8.
    :type encoding: ``str``
    '''
    def __init__(self,encoding='utf8',terminal='vt100',known_hosts=None,ssh_host_key_verification=enums.SSHHostKeyVerify.warn,
        ssh_keepalive_interval=0.0,set_flags={},method_preferences={},callbacks={},auto_terminate_tunnels=False,tcp_nodelay=False):
        self.debug = False
        self.client = self.pick_client()(encoding=encoding,terminal=terminal,known_hosts=known_hosts,
            ssh_host_key_verification=ssh_host_key_verification,ssh_keepalive_interval=ssh_keepalive_interval,set_flags=set_flags,method_preferences=method_preferences,
            callbacks=callbacks,auto_terminate_tunnels=auto_terminate_tunnels,tcp_nodelay=tcp_nodelay)

    def pick_client(self,ssh_client=None,custom_ssh_clients={}):
        default_client = clients.default_client
        if ssh_client==None:
            ssh_client = default_client
        client_pool = {}
        client_pool.update(clients.enabled_clients)
        client_pool.update(custom_ssh_clients)
        return(client_pool.get(ssh_client,clients.enabled_clients[default_client]))

    def eof(self):
        '''
        Returns ``True`` or ``False`` when the main channel has recieved an ``EOF``.
        '''
        return(self.client.eof())

    def methods(self, method):
        '''
        Returns what value was settled on during session negotiation.
        '''
        return(self.client.methods(method))

    def setenv(self, varname, value):
        '''
        Set an environment variable on the channel.

        :param varname: Name of environment variable to set on the remote channel.
        :type varname: ``str``
        :param value: Value to set ``varname`` to.
        :type value: ``str``
        :return: ``None``
        '''
        self.client.setenv(varname, value)

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
        self.client.before_connect_options()
        self.client.connect(hostname,port,username,password,allow_agent,host_based,key_filepath,passphrase,look_for_keys,sock,timeout)
        self.client.after_connect_options()

    def read(self,block=False):
        '''
        Recieve data from the remote session.
        Only works if the current session has made it past the login process.

        :param block: Block until data is received from the remote server. ``True``
            will block until data is recieved and ``False`` may return ``b''`` if no data is available from the remote server.
        :type block: ``bool``
        :return: ``generator`` - A generator of byte strings that has been recieved in the time given.
        '''
        return(self.client.read(block))

    def send(self,string):
        '''
        Send data to the remote session.
        Only works if the current session has made it past the login process.

        :param string: String to send to the remote session.
        :type string: ``str``
        :return: ``int`` - Amount of bytes sent to remote machine.
        '''
        return(self.client.send(string))

    def write(self,string):
        '''
        See :func:`redssh.RedSSH.send`
        '''
        return(self.send(string))

    def flush(self):
        '''
        Flush all data on the primary channel's stdin to the remote connection.
        Only works if connected, otherwise returns ``0``.

        :return: ``int`` - Amount of bytes sent to remote machine.
        '''
        if self.past_login==True:
            return(self.client.flush())
        return(0)

    def execute_command(self,command):
        '''
        Run a command. This will block as the command executes.

        :param command: Command to execute.
        :type command: ``str``
        :return: ``tuple (int, str)`` - of ``(return_code, command_output)``
        '''
        return(self.client.execute_command(command))

    def start_sftp(self):
        '''
        Start the SFTP client.
        The client will be available at `self.sftp` and will be an instance of `redssh.sftp.RedSFTP`

        :return: ``None``
        '''
        self.client.start_sftp()

    def start_scp(self):
        '''
        Start the SCP client.

        :return: ``None``
        '''
        self.client.start_scp()


    def forward_x11(self):
        '''
        Start forwarding an X11 display.

        :return: ``None``
        '''
        self.client.forward_x11()

    def local_tunnel(self,local_port,remote_host,remote_port,bind_addr='127.0.0.1',error_level=enums.TunnelErrorLevel.debug):
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
        return(self.client.local_tunnel(local_port,remote_host,remote_port,bind_addr,error_level))

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
        return(self.client.remote_tunnel(local_port,remote_host,remote_port,bind_addr,error_level))

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
        return(self.client.dynamic_tunnel(local_port,bind_addr,error_level))

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
        return(self.client.tunnel_is_alive(tunnel_type,sport,rhost,rport,bind_addr))

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
        self.client.close_tunnels(tunnel_type,sport,rhost,rport,bind_addr)


    def close_tunnels(self):
        '''
        Closes all SSH tunnels if any are open.
        '''
        self.client.close_tunnels()

    def exit(self):
        '''
        Kill the current session if connected.
        '''
        self.client.exit()
