import unittest
import threading
import multiprocessing
import paramiko
import redssh

from . import paramiko_server


class SSHSession(object):
    def __init__(self):
        self.rs = redssh.RedSSH()
        self.rs.connect('localhost', 2200, 'robey', 'foo')

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
        self.paramiko_server = threading.Thread(target=paramiko_server.start_server)
        self.paramiko_server.start()
        self.sshs = SSHSession()

    def tearDown(self):
        self.sshs.wait_for('Command: ')
        self.sshs.sendline('exit')
        self.sshs.wait_for('TEST')
        self.sshs.rs.exit()


    def test_basic_read_write(self):
        self.session_lock.acquire()
        self.sshs.wait_for('Command: ')
        self.sshs.sendline('reply')
        self.session_lock.release()


if __name__ == '__main__':
    unittest.main()

