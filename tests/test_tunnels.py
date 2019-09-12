import unittest
import threading
import multiprocessing
import requests
import paramiko
import redssh

from . import paramiko_server


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
        self.session_lock = multiprocessing.Lock()
        self.q = multiprocessing.Queue()
        self.paramiko_server = threading.Thread(target=paramiko_server.start_server,args=(self.q,))
        self.paramiko_server.start()
        self.sshs = SSHSession(self.q.get())

    def tearDown(self):
        self.session_lock.acquire()
        self.sshs.wait_for('Command: ')
        self.sshs.sendline('exit')
        self.sshs.wait_for('TEST')
        self.sshs.rs.exit()


    def test_basic_tunnel_read_write(self):
        self.session_lock.acquire()
        self.sshs.wait_for('Command: ')
        self.sshs.sendline('tunnel_test')
        # self.sshs.rs.forward_tunnel(2727,'google.com',80)
        # self.sshs.wait_for('Command: ')
        # print(requests.get('http://localhost:2727'))
        self.session_lock.release()


if __name__ == '__main__':
    unittest.main()

