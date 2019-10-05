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

def get_local(port):
    try:
        out = requests.get('http://localhost:'+str(port),timeout=(3,3)).text
        return(out)
    except Exception as e:
        print(e)


class RedSSHUnitTest(unittest.TestCase):

    def setUp(self):
        self.q = multiprocessing.Queue()
        self.server = multiprocessing.Process(target=ssh_server.start_server,args=(self.q,))
        self.server.start()
        self.server_hostname = 'localhost'
        self.server_port = self.q.get()
        self.ssh_sessions = []
        self.response_text = '<title>Error 404 (Not Found)!!1</title>'

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


    def test_local_tunnel_read_write(self):
        sshs = self.start_ssh_session()
        sshs.wait_for('Command$ ')
        sshs.sendline('local_tunnel_test')
        (a,b,server,port) = sshs.rs.local_tunnel(0,'google.com',80)
        sshs.wait_for('Tunneled')
        out = get_local(port)
        sshs.wait_for('Command$ ')
        assert self.response_text in out

    def test_remote_tunnel_read_write(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', 0))
        port = int(sock.getsockname()[1])
        sock.close()
        sshs = self.start_ssh_session()
        sshs.wait_for('Command$ ')
        sshs.sendline('remote_tunnel_test')
        sshs.rs.remote_tunnel(port,'google.com',80)
        sshs.wait_for('Tunneled')
        out = get_local(port)
        sshs.wait_for('Command$ ')
        assert self.response_text in out

    def test_local_remote_tunnels(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', 0))
        port = int(sock.getsockname()[1])
        sock.close()


        sshs = self.start_ssh_session()
        sshs.wait_for('Command$ ')
        sshs.sendline('remote_tunnel_test')
        sshs.rs.remote_tunnel(port,'google.com',80)
        sshs.wait_for('Tunneled')
        out = get_local(port)
        sshs.wait_for('Command$ ')
        assert self.response_text in out

        sshs.sendline('local_tunnel_test')
        (a,b,server,port) = sshs.rs.local_tunnel(0,'google.com',80)
        sshs.wait_for('Tunneled')
        out = get_local(port)
        sshs.wait_for('Command$ ')
        assert self.response_text in out



if __name__ == '__main__':
    unittest.main()

