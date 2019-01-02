"""
.. module:: redssh
   :platform: Unix
   :synopsis: Offers the RedSSH automation layer.

.. moduleauthor:: Red_M <redssh_docs@red-m.net>


"""

import re
import paramiko
import paramiko_expect

class RedSSH(object):
    def __init__(self,ssh_key_policy=None,prompt=r'.+?[#$]\s+',unique_prompt=False,encoding='utf8',**kwargs):
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
        self.PROMPT = self.prompt
        self.UNIQUE_PROMPT = r"\[PEXPECT\][\$\#] "
        self.PROMPT_SET_SH = r"PS1='[PEXPECT]\$ '"
        self.PROMPT_SET_CSH = r"set prompt='[PEXPECT]\$ '"
        self.expect = self.screen.expect
        self.sendline = self.screen.send
    
    def __check_for_attr__(self,attr):
        return(attr in self.__dict__)
    
    def set_ssh_key_policy(self,ssh_key_policy):
        self.client.set_missing_host_key_policy(ssh_key_policy)
    
    def connect(self,**kwargs):
        self.client.connect(**kwargs)
        self.screen = paramiko_expect.SSHClientInteraction(self.client, tty_width=0, tty_height=0, display=self.debug)
        self.screen.expect(self.prompt)
        self.past_login = True
        self.__pexpect_and_paramiko_expect_bind__()
        self.get_unique_prompt()
    
    def get_unique_prompt(self,use_basic_prompt=True):
        if use_basic_prompt==True:
            self.prompt = self.basic_prompt
        self.prompt = re.escape(self.command('',raw=True)[1:]) # A smart-ish way to get the current prompt after a dumb prompt match
    
    def command(self,cmd,raw=False):
        self.sendline(cmd)
        self.expect(self.prompt)
        if raw==False:
            out = self.screen.current_output_clean[:-1] # always adds a new line for whatever reason
        elif raw==True:
            out = self.screen.current_output
        return(out)
    
    def sudo(self,password,sudo=True,su_cmd='su -'):
        cmd = 'sudo'
        if sudo==False:
            cmd = su_cmd
        self.sendline(cmd)
        self.expect('[Pp]assword.+?')
        self.sendline(password)
        self.expect(self.basic_prompt)
        self.get_unique_prompt()
        
    
    def start_scp(self):
        if not self.__check_for_attr__('scp_client'):
            self.scp = self.client.open_sftp()
    
    def exit(self):
        if self.__check_for_attr__('past_login'):
            if self.past_login==True:
                self.client.close()
        
