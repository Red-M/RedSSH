import os
import socket
import subprocess
import unittest
import threading
import multiprocessing
import redssh

from .base_test import base_test as unittest_base


class RedSSHUnitTest(unittest_base):

    def test_agent_auth(self):
        try:
            if 'SSH_AUTH_SOCK' in os.environ:
                old_ssh_agent = os.environ['SSH_AUTH_SOCK']
                del os.environ['SSH_AUTH_SOCK']
            proc = subprocess.run('/usr/bin/ssh-agent',env=os.environ,capture_output=True,check=True,text=True)
            stdout = proc.stdout
            os.environ['SSH_AUTH_SOCK'] = stdout.split(';')[0].split('=')[-1]
            agent_pid = stdout.split(';')[-2].split(' ')[-1]
            subprocess.run(['/usr/bin/ssh-add',self.key_path],env=os.environ, check=True)
            sshs = self.start_ssh_session(class_init={},connect_args={'password':'','allow_agent':True})
            sshs.wait_for(self.prompt)
            sshs.sendline('echo')
            if 'old_ssh_agent' in locals():
                os.environ['SSH_AUTH_SOCK'] = old_ssh_agent
            subprocess.run(['/bin/kill',agent_pid],env=os.environ, check=True)
        except redssh.exceptions.AuthenticationFailedException:
            pass

    def test_no_auth_offered(self):
        failed = False
        try:
            sshs = self.start_ssh_session(class_init={},connect_args={'password':None,'allow_agent':False})
        except redssh.exceptions.NoAuthenticationOfferedException:
            failed = True
        assert failed==True

    def test_bad_agent_auth(self):
        try:
            sshs = self.start_ssh_session(class_init={},connect_args={'password':'','allow_agent':True})
            sshs.wait_for(self.prompt)
            sshs.sendline('echo')
        except redssh.exceptions.AuthenticationFailedException:
            pass

    def test_key_auth(self):
        sshs = self.start_ssh_session(class_init={},connect_args={'password':None,'allow_agent':False,'key_filepath':self.key_path})
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')

    def test_bad_key_auth(self):
        failed = False
        try:
            sshs = self.start_ssh_session(class_init={},connect_args={'password':'','allow_agent':False,'key_filepath':self.bad_key_path})
        except:
            failed = True
        assert(failed==True)

    def test_no_auth(self):
        failed = False
        try:
            sshs = self.start_ssh_session(class_init={},connect_args={'password':'','allow_agent':False,'key_filepath':None})
        except redssh.exceptions.AuthenticationFailedException:
            failed = True
        assert(failed==True)

if __name__ == '__main__':
    unittest.main()

