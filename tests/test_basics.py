import os
import time
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
        server_hostname = 'localhost'
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



    def test_basic_read_write(self):
        sshs = self.start_ssh_session()
        sshs.wait_for('Command$ ')
        sshs.sendline('reply')

    def test_known_hosts(self):
        known_hosts_file = os.path.join('tests','known_hosts')
        try:
            os.remove(known_hosts_file)
        except:
            pass
        for verify_level in redssh.enums.SSHHostKeyVerify:
            class_init = {
                'known_hosts':known_hosts_file,
                'ssh_host_key_verification': verify_level
            }
            try:
                sshs = self.start_ssh_session(class_init=class_init)
            except redssh.libssh2.exceptions.KnownHostCheckNotFoundError:
                assert verify_level==redssh.enums.SSHHostKeyVerify.strict
                continue
            sshs.wait_for('Command$ ')
            sshs.sendline('reply')
            sshs.wait_for('Command$ ')
            if verify_level==redssh.enums.SSHHostKeyVerify.auto_add:
                sshs2 = self.start_ssh_session(class_init=class_init)
                sshs2.wait_for('Command$ ')
                sshs2.sendline('reply')
                sshs2.wait_for('Command$ ')
            try:
                os.remove(known_hosts_file)
            except:
                pass

    def test_bring_your_own_socket(self):
        server_port = self.start_ssh_server()
        sock = socket.create_connection(('localhost',server_port),1)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
        sshs = self.start_ssh_session(server_port,class_init={},connect_args={'sock':sock})
        sshs.wait_for('Command$ ')
        sshs.sendline('reply')

    def test_ssh_keepalive(self):
        sshs = self.start_ssh_session(class_init={'ssh_keepalive_interval':1},connect_args={})
        sshs.wait_for('Command$ ')
        time.sleep(1)
        sshs.sendline('reply')
        sshs.wait_for('Command$ ')
        sshs.sendline('reply')


if __name__ == '__main__':
    unittest.main()

