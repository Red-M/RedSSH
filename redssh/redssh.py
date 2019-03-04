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


import os
import re
import threading
import paramiko
import paramiko_expect

from redssh import exceptions
from redssh import tunneling

class RedSSH(object):
    '''
    Instances the start of an SSH connection.
    Extra options are available at :func:`redssh.RedSSH.connect` time.

    :param ssh_key_policy: `paramiko`'s policy for handling server SSH keys. Defaults to :py:meth:`paramiko.client.SSHClient.RejectPolicy`
    :type ssh_key_policy: ``paramiko.client.SSHKeyPolicy``
    :param prompt: The basic prmopt to expect for the first command line.
    :type prompt: ``regex string``
    :param unique_prompt: Should a unique prompt be used for matching?
    :type unique_prompt: ``bool``
    :param encoding: Set the encoding to something other than the default of ``'utf8'`` when your target SSH server doesn't return UTF-8.
    :type encoding: ``str``
    '''
    def __init__(self,ssh_key_policy=None,prompt=r'.+?[\#\$]\s+',unique_prompt=False,encoding='utf8',**kwargs):
        self.debug = False
        self.unique_prompt = unique_prompt
        self.encoding = encoding
        self.basic_prompt = prompt
        self.prompt = prompt
        self.client = paramiko.SSHClient()
        if ssh_key_policy==None:
            self.set_ssh_key_policy(paramiko.RejectPolicy())
        else:
            self.set_ssh_key_policy(ssh_key_policy)
        self.quit = self.exit

    def __pexpect_and_paramiko_expect_bind__(self):
        '''
        This is an internal binder to make use of the pexpect function names for paramiko_expect.
        '''
        self.PROMPT = self.prompt
        self.UNIQUE_PROMPT = r"\[PEXPECT\][\$\#] "
        self.PROMPT_SET_SH = r" PS1='[PEXPECT]\$ '" #:
        self.PROMPT_SET_CSH = r" set prompt='[PEXPECT]\$ '"
        self.expect = self.screen.expect
        self.sendline = self.screen.send

    def __check_for_attr__(self,attr):
        return(attr in self.__dict__)

    def set_ssh_key_policy(self,ssh_key_policy):
        '''
        Just a shortcut for `paramiko.client.set_missing_host_key_policy`

        :param ssh_key_policy: `paramiko`'s policy for handling server SSH keys. Defaults to :py:meth:`paramiko.client.SSHClient.RejectPolicy`
        :type ssh_key_policy: `paramiko.client.SSHKeyPolicy`
        '''
        self.client.set_missing_host_key_policy(ssh_key_policy)

    def connect(self,**kwargs):
        '''
        All options for this is located in :py:meth:`paramiko.client.SSHClient.connect`
        '''
        self.client.connect(**kwargs)
        self.screen = paramiko_expect.SSHClientInteraction(self.client, tty_width=0, tty_height=0, display=self.debug)
        self.__pexpect_and_paramiko_expect_bind__() # do this early to make sure that users can call expected functions in the device_init.
        self.device_init()
        self.screen.expect(self.prompt)
        self.past_login = True
        self.set_unique_prompt()

    def forward_tunnel(self,local_port,remote_host,remote_port):
        '''
        Forwards a port the same way the ``-L`` option does for the OpenSSH client.
        '''
        transport = self.client.get_transport()
        class SubHander(tunneling.ForwardHandler):
            chain_host = remote_host
            chain_port = remote_port
            ssh_transport = transport
        tun_server = tunneling.ForwardServer(('',local_port),SubHander)
        tun_thread = threading.Thread(target=tun_server.serve_forever)
        tun_thread.daemon = True
        tun_thread.start()
        return(tun_thread)

    def reverse_tunnel(self,local_port,remote_host,remote_port):
        '''
        Forwards a port the same way the ``-R`` option does for the OpenSSH client.
        '''
        transport = self.client.get_transport()
        transport.request_port_forward('', local_port)
        def port_main(transport,remote_host,remote_port):
            while True:
                chan = transport.accept()
                if chan is None:
                    continue
                thr = threading.Thread(target=tunneling.reverse_handler, args=(chan, remote_host, remote_port))
                thr.setDaemon(True)
                thr.start()
        tun_thread = threading.Thread(target=port_main, args=(transport, remote_host, remote_port))
        tun_thread.setDaemon(True)
        tun_thread.start()
        return(tun_thread)

    def device_init(self,**kwargs):
        '''
        Override this function to intialize a device that does not simply drop to the terminal or a device will kick you out if you send any key/character other than an "acceptable" one.
        This default one will work on linux quite well but devices such as pfsense or mikrotik might require this function and :func:`redssh.RedSSH.get_unique_prompt` to be overriden.
        '''
        pass

    def get_unique_prompt(self):
        '''
        Return a unique prompt from the existing SSH session. Override this function to generate the compiled regex however you'd like, eg, from a database or from a hostname.

        :returns: compiled ``rstring``
        '''
        return(re.escape(self.command('',raw=True)[1:])) # A smart-ish way to get the current prompt after a dumb prompt match

    def set_unique_prompt(self,use_basic_prompt=True,set_prompt=False):
        '''
        Set a unique prompt in the existing SSH session.

        :param use_basic_prompt: Use the dumb prompt from first login to the remote terminal.
        :type use_basic_prompt: ``bool``
        :param set_prompt: Set to ``True`` to set the prompt via :var:`redssh.RedSSH.PROMPT_SET_SH`
        :type set_prompt: ``bool``
        '''
        if use_basic_prompt==True:
            self.prompt = self.basic_prompt
        if set_prompt==True:
            self.command(self.PROMPT_SET_SH)
        self.prompt = self.get_unique_prompt()

    def command(self,cmd,raw=False,prompt_change=False,reset_prompt=False):
        '''
        Run a command in the remote terminal.

        :param cmd: Command to execute, this will send characters exactly as if they were typed. (crtl+c could be sent via this).
        :type cmd: ``str``
        :param raw: Set to ``True`` to remove the "smart" cleaning, useful for debugging or for when you want the prompt as well.
        :type raw: ``bool``
        :param prompt_change: Set to ``True`` when the command executed changes the prompt to expect for when the command finishes, so that the prompt value is automatically set for you.
        :type prompt_change: ``bool``
        :param reset_prompt: Set to ``True`` to allow when ``prompt_change`` is set to ``True`` to set the prompt via :var:`redssh.RedSSH.PROMPT_SET_SH`.
        :type reset_prompt: ``bool``
        '''
        self.sendline(cmd)

        if prompt_change==True:
            self.expect(self.basic_prompt)
            self.set_unique_prompt(set_prompt=reset_prompt)
        elif prompt_change==False:
            self.expect(self.prompt)

        if raw==False:
            out = self.screen.current_output_clean[:-1] # always adds a new line for whatever reason
        elif raw==True:
            out = self.screen.current_output

        return(out)

    def sudo(self,password,sudo=True,su_cmd='su -'):
        '''
        Sudo up or SU up or whatever up into higher privileges.

        :param password: Password for gaining privileges
        :type password: ``str``
        :param sudo: Set to ``False`` to allow ``su_cmd`` to be executed instead.
        :type sudo: ``bool``
        :param su_cmd: Command to be executed when ``sudo`` is ``False``, allows overriding of the ``'sudo'`` default.
        :type su_cmd: ``str``
        :return: ``None``
        :raises: `redssh.BadSudoPassword`
        '''
        cmd = 'sudo'
        reg = r'.+?asswor.+?\:\s+'
        if sudo==False:
            cmd = su_cmd
        self.sendline(cmd)
        self.expect(reg)
        self.sendline(password)
        result = self.expect(re_strings=[self.basic_prompt,reg,r'Sorry.+?\.',r'.+?Authentication failure'])
        if result==0:
            self.set_unique_prompt()
        else:
            raise exceptions.BadSudoPassword()


    def start_scp(self):
        '''
        Start the SFTP client.
        '''
        if not self.__check_for_attr__('sftp_client'):
            self.sftp_client = self.client.open_sftp()

    def put_folder(self,local_path,remote_path,recursive=False):
        '''
        Upload an entire folder via SFTP to the remote session. Similar to `cp /files/* /target`
        Also retains file permissions.

        .. warning::

        Do note that this will only upload with the user you logged in as, not the current user you are running commands as.

        :param local_path: The local path, on the machine where your code is running from, to upload from.
        :type local_path: ``str``
        :param remote_path: The remote path to upload the ``local_path`` to.
        :type remote_path: ``str``
        :param recursive: Enable recursion down multiple directories from the top level of ``local_path``.
        :type recursive: ``bool``
        '''
        if self.__check_for_attr__('sftp_client'):
            for dirpath, dirnames, filenames in os.walk(local_path):
                for dirname in dirnames:
                    local_dir_path = os.path.join(local_path, dirname)
                    remote_dir_path = os.path.join(remote_path, dirname)
                    if not dirname in self.sftp_client.listdir(remote_path):
                        self.sftp_client.mkdir(remote_dir_path,os.stat(local_dir_path).st_mode)
                    if recursive==True:
                        self.put_folder(local_dir_path,remote_dir_path,recursive)
                for filename in filenames:
                    local_file_path = os.path.join(dirpath, filename)
                    remote_file_path = os.path.join(remote_path, filename)
                    if os.path.sep.join(local_file_path.split(os.path.sep)[:-1])==local_path:
                        self.put_file(local_file_path,remote_file_path)

    def put_file(self,local_path,remote_path):
        '''
        Upload file via SFTP to the remote session. Similar to ``cp /files/file /target``.
        Also retains file permissions.

        .. warning::

        Do note that this will only upload with the user you logged in as, not the current user you are running commands as.

        :param local_path: The local path, on the machine where your code is running from, to upload from.
        :type local_path: ``str``
        :param remote_path: The remote path to upload the ``local_path`` to.
        :type remote_path: ``str``
        '''
        if self.__check_for_attr__('sftp_client'):
            self.sftp_client.put(local_path,remote_path)
            self.sftp_client.chmod(remote_path,os.stat(local_path).st_mode)

    def exit(self):
        '''
        Kill the current session if actually connected.
        After this you might as well just free memory from the class instance.
        '''
        if self.__check_for_attr__('past_login'):
            if self.past_login==True:
                self.client.close()
