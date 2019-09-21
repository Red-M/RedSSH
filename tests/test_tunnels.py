import socket
import unittest
import threading
import multiprocessing
import requests
import redssh
import time

from . import paramiko_server as ssh_server


class SSHSession(object):
    def __init__(self,hostname='localhost',port=2200):
        self.rs = redssh.RedSSH()
        self.rs.connect('localhost', port, 'redm', 'foobar!')

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
        self.q = multiprocessing.Queue()
        self.server = multiprocessing.Process(target=ssh_server.start_server,args=(self.q,))
        self.server.start()
        self.server_hostname = 'localhost'
        self.server_port = self.q.get()
        self.ssh_sessions = []

    def start_ssh_session(self):
        sshs = SSHSession(self.server_hostname,self.server_port)
        self.ssh_sessions.append(sshs)
        return(sshs)

    def end_ssh_session(self,sshs):
        sshs.sendline('exit')
        sshs.wait_for('TEST')
        sshs.rs.exit()

    def tearDown(self):
        for session in self.ssh_sessions:
            self.end_ssh_session(session)
        self.server.kill()


    def test_basic_tunnel_read_write(self):
        port = 2727
        sshs = self.start_ssh_session()
        sshs.wait_for('Command$ ')
        sshs.sendline('tunnel_test')
        sshs.rs.forward_tunnel(port,'google.com',80)
        sshs.wait_for('Tunneled')
        print(requests.get('http://localhost:'+str(port)))
        sshs.wait_for('Command$ ')


if __name__ == '__main__':
    unittest.main()

