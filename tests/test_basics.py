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
        self.rs.connect(hostname, port, 'redm', 'foobar!',**connect_args)

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
        self.ssh_servers = []
        self.ssh_sessions = []

    def start_ssh_server(self):
        q = multiprocessing.Queue()
        server = multiprocessing.Process(target=ssh_server.start_server,args=(q,))
        server.start()
        self.ssh_servers.append(server)
        server_port = q.get()
        return(server_port)

    def start_ssh_session(self,server_port=None,class_init={},connect_args={}):
        server_hostname = 'localhost'
        if server_port==None:
            server_port = self.start_ssh_server()
        sshs = SSHSession(server_hostname,server_port,class_init,connect_args)
        self.ssh_sessions.append(sshs)
        return(sshs)

    def end_ssh_session(self,sshs):
        sshs.rs.exit()

    def tearDown(self):
        for session in self.ssh_sessions:
            self.end_ssh_session(session)
        for server in self.ssh_servers:
            server.kill()



    def test_basic_read_write(self):
        sshs = self.start_ssh_session()
        sshs.wait_for('Command$ ')
        sshs.sendline('reply')

    def test_known_hosts(self):
        sshs = self.start_ssh_session(class_init={'known_hosts':os.path.join(os.path.expanduser('~'),'.ssh','known_hosts')})
        sshs.wait_for('Command$ ')
        sshs.sendline('reply')

    def test_key_agent(self):
        sshs = self.start_ssh_session(class_init={},connect_args={'allow_agent':True})
        sshs.wait_for('Command$ ')
        sshs.sendline('reply')

    def test_bring_your_own_socket(self):
        server_port = self.start_ssh_server()
        sock = socket.create_connection(('localhost',server_port),1)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
        sshs = self.start_ssh_session(server_port,class_init={},connect_args={'sock':sock})
        sshs.wait_for('Command$ ')
        sshs.sendline('reply')


if __name__ == '__main__':
    unittest.main()

