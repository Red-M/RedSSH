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
'''
.. module:: redssh
   :platform: Unix
   :synopsis: Offers the RedSSH automation layer.

.. moduleauthor:: Red_M <redssh_docs@red-m.net>


'''

import os
import re
import paramiko
import paramiko_expect

class RedSSH(object):
    def __init__(self,ssh_key_policy=None,prompt=r'.+?[#$]\s+',unique_prompt=False,encoding='utf8',**kwargs):
        '''
        '''
        self.debug = False
        self.encoding = encoding
        self.basic_prompt = prompt
        self.prompt = prompt
        self.unique_prompt = unique_prompt
        self.client = paramiko.SSHClient()
        if ssh_key_policy==None:
            self.set_ssh_key_policy(paramiko.RejectPolicy())
        else:
            self.set_ssh_key_policy(ssh_key_policy)
        self.quit = self.exit
    
    def __pexpect_and_paramiko_expect_bind__(self):
        '''
        '''
        self.PROMPT = self.prompt
        self.UNIQUE_PROMPT = r"\[PEXPECT\][\$\#] "
        self.PROMPT_SET_SH = r" PS1='[PEXPECT]\$ '"
        self.PROMPT_SET_CSH = r" set prompt='[PEXPECT]\$ '"
        self.expect = self.screen.expect
        self.sendline = self.screen.send
    
    def __check_for_attr__(self,attr):
        '''
        '''
        return(attr in self.__dict__)
    
    def set_ssh_key_policy(self,ssh_key_policy):
        '''
        '''
        self.client.set_missing_host_key_policy(ssh_key_policy)
    
    def connect(self,**kwargs):
        '''
        '''
        self.client.connect(**kwargs)
        self.screen = paramiko_expect.SSHClientInteraction(self.client, tty_width=0, tty_height=0, display=self.debug)
        self.screen.expect(self.prompt)
        self.past_login = True
        self.__pexpect_and_paramiko_expect_bind__()
        self.set_unique_prompt()
    
    def get_unique_prompt(self):
        '''
        '''
        return(re.escape(self.command('',raw=True)[1:])) # A smart-ish way to get the current prompt after a dumb prompt match
    
    def set_unique_prompt(self,use_basic_prompt=True,set_prompt=False):
        '''
        '''
        if use_basic_prompt==True:
            self.prompt = self.basic_prompt
        if set_prompt==True:
            self.command(self.PROMPT_SET_SH)
        self.prompt = self.get_unique_prompt()
    
    def command(self,cmd,raw=False,prompt_change=False,reset_prompt=False):
        '''
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
        '''
        cmd = 'sudo'
        if sudo==False:
            cmd = su_cmd
        self.sendline(cmd)
        self.expect('.+?asswor.+?\s+')
        self.sendline(password)
        self.expect(self.basic_prompt)
        self.set_unique_prompt()
        
    
    def start_scp(self):
        '''
        '''
        if not self.__check_for_attr__('sftp_client'):
            self.sftp_client = self.client.open_sftp()
    
    def put_folder(self,local_path,remote_path,recursive=False):
        '''
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
        '''
        if self.__check_for_attr__('sftp_client'):
            self.sftp_client.put(local_path,remote_path)
            self.sftp_client.chmod(remote_path,os.stat(local_path).st_mode)
    
    def exit(self):
        '''
        '''
        if self.__check_for_attr__('past_login'):
            if self.past_login==True:
                self.client.close()
        
