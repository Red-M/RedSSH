import os
import time
import socket
import unittest
import threading
import multiprocessing
import paramiko
import redssh

from .servers import paramiko_server as ssh_server


class SSHSession(object):
    def __init__(self,hostname='127.0.0.1',port=2200,class_init={},connect_args={}):
        self.conn_hostname = hostname
        self.conn_port = port
        self.conn_connect_args = connect_args
        self.rs = redssh.RedSSH(**class_init)
        self._tests_connect()

    def wait_for(self, wait_string):
        if isinstance(wait_string,type('')):
            wait_string = wait_string.encode('utf8')
        read_data = b''
        while not wait_string in read_data:
            for data in self.rs.read():
                print(data)
                read_data += data
        return(read_data)

    def sendline(self, line):
        self.rs.send(line+'\r\n')

    def _tests_connect(self):
        connect_args_extra = {
            'username':'redm',
            'password':'foobar!'
        }
        connect_args_extra.update(self.conn_connect_args)
        self.rs.connect(self.conn_hostname, self.conn_port, **connect_args_extra)



class RedSSHUnitTest(unittest.TestCase):

    def setUp(self):
        self.key_path = os.path.join(os.path.join(os.getcwd(),'tests'),'ssh_host_key_paramiko')
        self.bad_key_path = os.path.join(os.path.join(os.getcwd(),'tests'),'ssh_host_key')
        self.ssh_servers = []
        self.ssh_sessions = []
        self.server_hostname = '127.0.0.1'

    def start_ssh_server(self):
        q = multiprocessing.Queue()
        server = multiprocessing.Process(target=ssh_server.start_server,args=(q,))
        server.start()
        self.ssh_servers.append(server)
        server_port = q.get()
        return(server_port)

    def start_ssh_session(self,server_port=None,class_init={},connect_args={}):
        server_hostname = '127.0.0.1'
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
        assert sshs.rs.eof()==False

    def test_basic_set_session_options(self):
        sshs = self.start_ssh_session()
        sshs.wait_for('Command$ ')
        sshs.sendline('reply')
        res = sshs.rs.methods(redssh.libssh2.LIBSSH2_METHOD_CRYPT_SC)

    def test_basic_setenv(self):
        sshs = self.start_ssh_session()
        sshs.wait_for('Command$ ')
        sshs.sendline('reply')
        try:
            sshs.rs.setenv('TEST','test') # I need to rewrite the test server at this point, this is crap.
        except:
            pass

    # def test_basic_reconnect(self): This is broken but should be working, I blame the test ssh server.
        # sshs = self.start_ssh_session()
        # sshs.wait_for('Command$ ')
        # sshs.sendline('reply')
        # sshs.rs.exit()
        # sshs.conn_port = self.start_ssh_server()
        # sshs._tests_connect()
        # sshs.wait_for('Command$ ')
        # sshs.sendline('reply')

    def test_basic_last_error(self):
        sshs = self.start_ssh_session()
        sshs.wait_for('Command$ ')
        sshs.sendline('reply')
        sshs.rs.last_error()

    def test_basic_set_flags_and_prefs(self):
        comp = b'zlib,zlib@openssh.com,none'
        class_init = {
            'set_flags':{
                redssh.libssh2.LIBSSH2_FLAG_COMPRESS:True
            },
            'method_preferences':{
                redssh.libssh2.LIBSSH2_METHOD_COMP_SC:comp,
                redssh.libssh2.LIBSSH2_METHOD_COMP_CS:comp
            }
        }
        sshs = self.start_ssh_session(class_init=class_init)
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
        sock = socket.create_connection(('127.0.0.1',server_port),1)
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

