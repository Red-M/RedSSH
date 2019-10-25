import os
import socket
import unittest
import threading
import multiprocessing
import paramiko
import redssh

from . import paramiko_server as ssh_server


class SSHSession(object):
    def __init__(self,hostname='localhost',port=2200,class_init={},connect_args={}):
        self.rs = redssh.RedSSH(**class_init)
        connect_args_extra = {
            'username':'redm',
            'password':'foobar!'
        }
        connect_args_extra.update(connect_args)
        self.rs.connect(hostname, port, **connect_args_extra)

    def wait_for(self, wait_string):
        if isinstance(wait_string,type('')):
            wait_string = wait_string.encode('utf8')
        read_data = b''
        while not wait_string in read_data:
            for data in self.rs.read():
                read_data += data
        return(read_data)

    def sendline(self, line):
        self.rs.send(line+'\r\n')



class RedSSHUnitTest(unittest.TestCase):

    def setUp(self):
        self.key_path = os.path.join(os.path.join(os.getcwd(),'tests'),'ssh_host_key_paramiko')
        self.bad_key_path = os.path.join(os.path.join(os.getcwd(),'tests'),'ssh_host_key')
        self.ssh_servers = []
        self.ssh_sessions = []
        self.server_hostname = 'localhost'

    def start_ssh_server(self):
        q = multiprocessing.Queue()
        server = multiprocessing.Process(target=ssh_server.start_server,args=(q,))
        server.start()
        self.ssh_servers.append(server)
        server_port = q.get()
        return(server_port)

    def start_ssh_session(self,server_port=None,class_init={},connect_args={}):
        if server_port==None:
            server_port = self.start_ssh_server()
        sshs = SSHSession(self.server_hostname,server_port,class_init,connect_args)
        self.ssh_sessions.append(sshs)
        return(sshs)

    def end_ssh_session(self,sshs):
        sshs.sendline('exit')
        sshs.wait_for('TEST')
        sshs.rs.exit()

    def tearDown(self):
        for session in self.ssh_sessions:
            self.end_ssh_session(session)
        for server in self.ssh_servers:
            server.kill()



    def test_agent_auth(self):
        try:
            # spawn ssh agent and remove potiental for agent already in environ
            sshs = self.start_ssh_session(class_init={},connect_args={'password':'','allow_agent':True})
            sshs.wait_for('Command$ ')
            sshs.sendline('reply')
        except redssh.exceptions.AuthenticationFailedException:
            pass

    def test_key_auth(self):
        sshs = self.start_ssh_session(class_init={},connect_args={'password':None,'allow_agent':False,'key_filepath':self.key_path})
        sshs.wait_for('Command$ ')
        sshs.sendline('reply')

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
            sshs = self.start_ssh_session(class_init={},connect_args={'password':'','allow_agent':False})
        except redssh.exceptions.AuthenticationFailedException:
            failed = True
        assert(failed==True)

if __name__ == '__main__':
    unittest.main()

