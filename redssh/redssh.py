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
import multiprocessing
import socket
from ssh2.session import Session as ssh2_session
from ssh2.sftp import LIBSSH2_FXF_TRUNC, LIBSSH2_FXF_WRITE, LIBSSH2_FXF_CREAT


from redssh import exceptions
from redssh import tunneling


class RedSSH(object):
    '''
    Instances the start of an SSH connection.
    Extra options are available at :func:`redssh.RedSSH.connect` time.

    :param prompt: The basic prompt to expect for the first command line.
    :type prompt: ``regex string``
    :param unique_prompt: Should a unique prompt be used for matching?
    :type unique_prompt: ``bool``
    :param encoding: Set the encoding to something other than the default of ``'utf8'`` when your target SSH server doesn't return UTF-8.
    :type encoding: ``str``
    :param newline: Set the newline for sending and recieving text to the remote server to something other than the default of ``'\\r'``.
    :type newline: ``str``
    :param terminal: Set the terminal sent to the remote server to something other than the default of ``'vt100'``.
    :type terminal: ``str``
    '''
    def __init__(self,prompt=r'.+?[\#\$]\s+',unique_prompt=False,encoding='utf8',newline='\r',terminal='vt100'):
        self.debug = False
        self.unique_prompt = unique_prompt
        self.encoding = encoding
        self.basic_prompt = prompt
        self.prompt_regex = prompt
        self.tunnels = {'local':{},'remote':{}}
        self.current_send_string = ''
        self.current_output = ''
        self.current_output_clean = ''
        self.newline = newline
        self.terminal = terminal

    def __check_for_attr__(self,attr):
        return(attr in self.__dict__)

    def connect(self,hostname, port=22, username=None, password=None, pkey=None, key_filename=None, timeout=None,
        allow_agent=True, look_for_keys=True, compress=False, sock=None, gss_auth=False, gss_kex=False, gss_deleg_creds=True,
        gss_host=None, banner_timeout=None, auth_timeout=None, gss_trust_dns=True, passphrase=None):
        '''
        Most of these options will work soon but for now only SSH keys via an SSH agent will work.

        :param hostname: Hostname to connect to.
        :type hostname: ``str``
        :param port: SSH port to connect to.
        :type port: ``int``
        :param username: Username to connect as to the remote server.
        :type username: ``str``
        '''
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((hostname, port))
        self.session = ssh2_session()
        self.session.handshake(self.sock)
        self.session.agent_auth(username)
        if allow_agent==True:
            agent = self.session.agent_init()
            agent.connect()
            identities = agent.get_identities()
            del agent
        self.channel = self.session.open_session()
        self.channel.pty(self.terminal)
        self.channel.shell()
        self.past_login = True
        self.device_init()
        self.expect(self.prompt_regex)
        self.set_unique_prompt()

    def prompt(self):
        '''
        Get a command line prompt in the terminal.
        Useful for using :func:`redssh.RedSSH.sendline` to send commands
        then using this for when you want to get back to a prompt.
        '''
        self.expect(self.prompt_regex)

    def sendline_raw(self,string):
        '''
        Use this when you want to directly interact with the remote session.

        :param string: String to send to the remote session.
        :type string: ``str``
        '''
        self.channel.write(string)

    def sendline(self,send_string,newline=None):
        '''
        Saves and sends the send string provided to the remote session with a newline added.

        :param send_string: String to send to the remote session.
        :type send_string: ``str``
        :param newline: Override the newline character sent to the remote session.
        :type newline: ``str``
        '''
        self.current_send_string = send_string
        if not newline==None:
            newline = newline
        else:
            newline = self.newline
        self.sendline_raw(send_string+newline)

    def remote_text_clean(self,string,strip_ansi=True):
        string = string.replace('\r','')
        if strip_ansi==True:
            string = re.sub(r'\x1b\[([0-9,A-Z]{1,2}(;[0-9]{1,2})?(;[0-9]{3})?)?[m|K]?','',string)
        return(string)

    def expect(self, re_strings='',default_match_prefix='.*\n',strip_ansi=True):
        '''
        This function takes in a regular expression (or regular expressions)
        that represent the last line of output from the server.  The function
        waits for one or more of the terms to be matched.  The regexes are
        matched using expression ``r'\\n<regex>$'`` so you'll need to provide an
        easygoing regex such as ``'.*server.*'`` if you wish to have a fuzzy
        match.

        This has been originally taken from paramiko_expect and modified to work with ssh2-python plus my own additions and redactions.
        I've also made the style consistent with the rest of the library.

        :param re_strings: Either a regex string or list of regex strings
                           that we should expect; if this is not specified,
                           then ``EOF`` is expected (i.e. the shell is completely
                           closed after the exit command is issued)
        :param default_match_prefix: A prefix to all match regexes, defaults to ``'.*\\n'``,
                                     can set to ``''`` on cases prompt is the first line,
                                     or the command has no output.
        :param strip_ansi: If ``True``, will strip ansi control chars befores regex matching
                           default to True.
        :return: ``int`` - An ``EOF`` returns ``-1``, a regex metch returns ``0`` and a match in a
                 list of regexes returns the index of the matched string in
                 the list.
        '''
        self.current_output = ''

        if isinstance(re_strings,str) and len(re_strings)!=0:
            re_strings = [re_strings]

        while (len(re_strings)==0 or not [re_string for re_string in re_strings if re.match(default_match_prefix+re_string+'$',self.current_output,re.DOTALL)]):
            (err_code,current_buffer) = self.channel.read()

            if len(current_buffer)==0:
                break

            current_buffer_decoded = self.remote_text_clean(current_buffer.decode(self.encoding),strip_ansi=True)
            self.current_output += current_buffer_decoded

        if len(re_strings)!=0:
            found_pattern = [(re_index, re_string) for (re_index,re_string) in enumerate(re_strings) if re.match(default_match_prefix+re_string+'$',self.current_output,re.DOTALL)]

        self.current_output_clean = self.current_output

        if len(self.current_send_string)!=0:
            self.current_output_clean = self.current_output_clean.replace(self.current_send_string+'\n','')
        self.current_send_string = ''

        if len(re_strings)!=0 and len(found_pattern)!=0:
            self.current_output_clean = re.sub(found_pattern[0][1]+'$','',self.current_output_clean)
            self.last_match = found_pattern[0][1]
            return(found_pattern[0][0])
        else:
            return(-1)


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
        return(re.escape(self.command('',clean_output=False)[1:])) # A smart-ish way to get the current prompt after a dumb prompt match

    def set_unique_prompt(self,use_basic_prompt=True,set_prompt=False):
        '''
        Set a unique prompt in the existing SSH session.

        :param use_basic_prompt: Use the dumb prompt from first login to the remote terminal.
        :type use_basic_prompt: ``bool``
        :param set_prompt: Set to ``True`` to set the prompt via :var:`redssh.RedSSH.PROMPT_SET_SH`
        :type set_prompt: ``bool``
        '''
        if use_basic_prompt==True:
            self.prompt_regex = self.basic_prompt
        if set_prompt==True:
            self.command(self.prompt_regex_SET_SH)
        self.prompt_regex = self.get_unique_prompt()

    def command(self,cmd,clean_output=True,remove_newline=False):
        '''
        Run a command in the remote terminal.

        :param cmd: Command to execute, this will send characters exactly as if they were typed. (crtl+c could be sent via this).
        :type cmd: ``str``
        :param clean_output: Set to ``False`` to remove the "smart" cleaning, useful for debugging or for when you want the prompt as well.
        :type clean_output: ``bool``
        :param remove_newline: Set to ``True`` to remove the last newline on a return, useful when a command adds a newline to its output.
        :type remove_newline: ``bool``

        :returns: ``str``
        '''
        self.sendline(cmd)
        self.prompt()
        if clean_output==True:
            out = self.current_output_clean
        else:
            out = self.current_output
        if remove_newline==True:
            if out.endswith('\n'):
                out = out[:-1]
        return(out)


    def sudo(self,password,sudo=True,su_cmd='su -'):
        '''
        Sudo up or SU up or whatever up, into higher privileges.

        :param password: Password for gaining privileges
        :type password: ``str``
        :param sudo: Set to ``False`` to allow ``su_cmd`` to be executed instead.
        :type sudo: ``bool``
        :param su_cmd: Command to be executed when ``sudo`` is ``False``, allows overriding of the ``'sudo'`` default.
        :type su_cmd: ``str``
        :return: ``None``
        :raises: :class:`redssh.exceptions.BadSudoPassword` if the password provided does not allow for privilege escalation.
        '''
        cmd = su_cmd
        reg = r'.+?asswor.+?\:\s+'
        if sudo==True:
            cmd = 'sudo '+su_cmd
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
            self.sftp_client = self.session.sftp_init()

    def put_folder(self,local_path,remote_path,recursive=False):
        '''
        Upload an entire folder via SFTP to the remote session. Similar to ``cp /files/* /target``
        Also retains file permissions.

        .. warning::
            This will only upload with the user you logged in as, not the current user you are running commands as.

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
                    if not dirname in self.sftp_client.opendir(remote_path).readdir():
                        try:
                            self.sftp_client.mkdir(remote_dir_path,os.stat(local_dir_path).st_mode)
                        except Exception as e:
                            pass
                    if recursive==True:
                        self.put_folder(local_dir_path,remote_dir_path,recursive=recursive)
                for filename in filenames:
                    local_file_path = os.path.join(dirpath, filename)
                    remote_file_base = local_file_path[len(local_path):0-len(filename)]
                    if remote_file_base.startswith('/'):
                        remote_file_base = remote_file_base[1:]
                    remote_file_path = os.path.join(os.path.join(remote_path,remote_file_base),filename)
                    self.put_file(local_file_path,remote_file_path)

    def put_file(self,local_path,remote_path):
        '''
        Upload file via SFTP to the remote session. Similar to ``cp /files/file /target``.
        Also retains file permissions.

        .. warning::
            This will only upload with the user you logged in as, not the current user you are running commands as.

        :param local_path: The local path, on the machine where your code is running from, to upload from.
        :type local_path: ``str``
        :param remote_path: The remote path to upload the ``local_path`` to.
        :type remote_path: ``str``
        '''
        if self.__check_for_attr__('sftp_client'):
            self.sftp_client.open(remote_path,LIBSSH2_FXF_WRITE|LIBSSH2_FXF_CREAT|LIBSSH2_FXF_TRUNC,os.stat(local_path).st_mode).write(open(local_path,'rb').read())


    def forward_tunnel(self,local_port,remote_host,remote_port,bind_addr=''):
        '''
        .. warning::
            This is broken in this commit. Will be fixed once https://github.com/ParallelSSH/parallel-ssh/issues/140 has some sort of resolution.


        Forwards a port the same way the ``-L`` option does for the OpenSSH client.

        :param local_port: The local port on the local machine to connect to.
        :type local_port: ``int``
        :param remote_host: The remote host to connect to via the remote machine.
        :type remote_host: ``str``
        :param remote_port: The remote host's port to connect to via the remote machine.
        :type remote_port: ``int``
        :param bind_addr: The bind address on this machine to bind to for the local port.
        :type bind_addr: ``str``
        :return: ``tuple`` of ``(tun_thread,thread_queue,tun_server)`` this is so you can control the tunnel's thread if you need to.
        '''
        return()
        option_string = str(local_port)+':'+remote_host+':'+str(remote_port)
        if not option_string in self.tunnels['local']:
            ssh_transport = self.session
            thread_queue = multiprocessing.Queue()

            class SubHander(tunneling.ForwardHandler):
                chain_host = remote_host
                chain_port = remote_port
                session = ssh_transport
                queue = thread_queue
                src_tup = (bind_addr,local_port)
                dst_tup = (remote_host,remote_port)
                channel_retries = 5
                num_retries = 3

            tun_server = tunneling.ForwardServer((bind_addr,local_port),SubHander)
            tun_thread = threading.Thread(target=tun_server.serve_forever)
            tun_thread.daemon = True
            tun_thread.name = option_string
            tun_thread.start()
            self.tunnels['local'][option_string] = (tun_thread,thread_queue,tun_server)
        return(self.tunnels['local'][option_string])

    def reverse_tunnel(self,local_port,remote_host,remote_port):
        '''
        .. warning::
            This is broken in this commit. Will be fixed later.


        Forwards a port the same way the ``-R`` option does for the OpenSSH client.

        :param local_port: The local port on the remote side to connect to.
        :type local_port: ``int``
        :param remote_host: The remote host to connect to via the local machine.
        :type remote_host: ``str``
        :param remote_port: The remote host's port to connect to via the local machine.
        :type remote_port: ``int``
        :return: ``tuple`` of ``(tun_thread,thread_queue,None)`` this is so you can control the tunnel's thread if you need to.
        '''
        return()
        option_string = str(local_port)+':'+remote_host+':'+str(remote_port)
        if not option_string in self.tunnels['remote']:
            transport = self.session.open_session()
            transport.request_port_forward('', local_port)
            thread_queue = multiprocessing.Queue()
            def port_main(transport,remote_host,remote_port,queue):
                while True:
                    chan = transport.accept(1)
                    if not chan==None:
                        thr = threading.Thread(target=tunneling.reverse_handler, args=(chan, remote_host, remote_port))
                        thr.daemon = True
                        thr.start()
                    try:
                        if queue.get(False)=='terminate':
                            break
                    except Exception as e:
                        pass
            tun_thread = threading.Thread(target=port_main, args=(transport, remote_host, remote_port, thread_queue))
            tun_thread.daemon = True
            tun_thread.name = option_string
            tun_thread.start()
            self.tunnels['remote'][option_string] = (tun_thread,thread_queue,None)
        return(self.tunnels['remote'][option_string])


    def close_tunnels(self):
        '''
        Closes all tunnels if any are open.
        '''
        for thread_type in self.tunnels:
            for option_string in self.tunnels[thread_type]:
                try:
                    (thread,queue,server) = self.tunnels[thread_type][option_string]
                    queue.put('terminate')
                    if not server==None:
                        server.shutdown()
                    if thread.is_alive():
                        thread.join()
                except Exception as e:
                    pass

    def exit(self):
        '''
        Kill the current session if actually connected.
        After this you might as well just free memory from the class instance.
        '''
        if self.__check_for_attr__('past_login'):
            self.close_tunnels()
            if self.past_login==True:
                self.channel.close()
                self.session.disconnect()
                self.sock.close()
