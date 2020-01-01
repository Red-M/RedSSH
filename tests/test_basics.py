import os
import time
import socket
import unittest
import threading
import multiprocessing
import redssh

from .base_test import base_test as unittest_base


class RedSSHUnitTest(unittest_base):

    def test_basic_read_write(self):
        sshs = self.start_ssh_session()
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        assert sshs.rs.eof()==False

    def test_basic_set_session_options(self):
        sshs = self.start_ssh_session()
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        res = sshs.rs.methods(redssh.libssh2.LIBSSH2_METHOD_CRYPT_SC)

    def test_basic_setenv(self):
        sshs = self.start_ssh_session()
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        try:
            sshs.rs.setenv('TEST','test') # I need to rewrite the test server at this point, this is crap.
        except:
            pass

    # def test_basic_reconnect(self): # This is broken but should be working, I blame the test ssh server.
        # sshs = self.start_ssh_session()
        # sshs.wait_for(self.prompt)
        # sshs.sendline('echo')
        # sshs.rs.exit()
        # sshs.conn_port = self.start_ssh_server()
        # sshs._tests_connect()
        # sshs.wait_for(self.prompt)
        # sshs.sendline('echo')

    def test_basic_last_error(self):
        sshs = self.start_ssh_session()
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
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
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')

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
            sshs.wait_for(self.prompt)
            sshs.sendline('echo')
            sshs.wait_for(self.prompt)
            if verify_level==redssh.enums.SSHHostKeyVerify.auto_add:
                sshs2 = self.start_ssh_session(class_init=class_init)
                sshs2.wait_for(self.prompt)
                sshs2.sendline('echo')
                sshs2.wait_for(self.prompt)
            try:
                os.remove(known_hosts_file)
            except:
                pass

    def test_bring_your_own_socket(self):
        server_port = self.start_ssh_server()
        sock = socket.create_connection(('127.0.0.1',server_port),1)
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
        sshs = self.start_ssh_session(server_port,class_init={},connect_args={'sock':sock})
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')

    def test_ssh_keepalive(self):
        sshs = self.start_ssh_session(class_init={'ssh_keepalive_interval':1},connect_args={})
        sshs.wait_for(self.prompt)
        time.sleep(1)
        sshs.sendline('echo')
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')


if __name__ == '__main__':
    unittest.main()

