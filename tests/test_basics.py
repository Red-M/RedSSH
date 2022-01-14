import os
import time
import socket
import pytest
import unittest
import threading
import multiprocessing
import redssh

from .base_test import base_test as unittest_base


class RedSSHUnitTest(unittest_base):

    def test_basic_read_write(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                sshs = self.start_ssh_session()
                sshs.wait_for(self.prompt)
                sshs.sendline('echo')
                assert sshs.rs.eof()==False

    def test_basic_set_session_options(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                sshs = self.start_ssh_session()
                sshs.wait_for(self.prompt)
                sshs.sendline('echo')
                if client=='LibSSH2':
                    res = sshs.rs.methods(redssh.libssh2.LIBSSH2_METHOD_CRYPT_SC)
                elif client=='LibSSH':
                    pass # TODO


    def test_basic_setenv(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                sshs = self.start_ssh_session()
                try:
                    sshs.rs.setenv('TEST','test') # There is something else at play here,
                    # this needs to be ran at a certain point in the session's lifetime.
                except:
                    pass
                sshs.wait_for(self.prompt)
                sshs.sendline('echo')

    # def test_basic_reconnect(self):
        # for client in sorted(redssh.clients.enabled_clients):
            # with self.subTest(client=client):
                # sshs = self.start_ssh_session()
                # sshs.wait_for(self.prompt)
                # sshs.sendline('echo')
                # sshs.wait_for(self.prompt)
                # sshs.rs.exit()
                # sshs.rs.connect(sshs.connected_hostname, sshs.connected_port,**sshs.connect_args)
                # sshs.wait_for(self.prompt)
                # sshs.sendline('echo')

    def test_basic_last_error(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                sshs = self.start_ssh_session()
                sshs.wait_for(self.prompt)
                sshs.sendline('echo')
                sshs.rs.last_error()

    def test_basic_set_flags_and_prefs(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                comp = b'zlib,zlib@openssh.com,none' # TODO redlibssh
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
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
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
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                server_port = self.start_ssh_server()
                sock = socket.create_connection(('127.0.0.1',server_port),1)
                sock.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
                sshs = self.start_ssh_session(server_port,class_init={},connect_args={'sock':sock})
                sshs.wait_for(self.prompt)
                sshs.sendline('echo')

    def test_ssh_keepalive(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                sshs = self.start_ssh_session(class_init={'ssh_keepalive_interval':1},connect_args={})
                sshs.wait_for(self.prompt)
                time.sleep(1)
                sshs.sendline('echo')
                sshs.wait_for(self.prompt)
                sshs.sendline('echo')


if __name__ == '__main__':
    unittest.main()

