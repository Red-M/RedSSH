import socket
import unittest
import threading
import multiprocessing
import requests
import redssh
import time

from . import asyncssh_server


class SSHSession(object):
    def __init__(self,port=2200):
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
        self.server = multiprocessing.Process(target=asyncssh_server.start_server,args=(self.q,))
        self.server.start()
        time.sleep(0.5)
        self.server_port = self.q.get()
        self.ssh_sessions = []

    def start_ssh_session(self):
        sshs = SSHSession(self.server_port)
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
        sshs = self.start_ssh_session()
        sshs.wait_for('Command$ ')
        sshs.sendline('tunnel_test')
        port = 2727
        sshs.rs.forward_tunnel(port,'localhost',port) # This is due to the test server implementation.
        sshs.wait_for('Command$ ')
        sock = socket.create_connection(('localhost',port),1)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
        test_string = b'thisisatest'
        sock.send(test_string)
        result = sock.recv(1024)
        assert result==test_string


if __name__ == '__main__':
    unittest.main()

