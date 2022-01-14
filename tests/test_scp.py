import os
import time
import socket
import shutil
import unittest
import threading
import multiprocessing
import redssh

from .base_test import base_test as unittest_base


class RedSSHUnitTest(unittest_base):

    def test_open_scp(self):
        for client in sorted(['LibSSH2']): #Remove when libssh implements nonblocking SFTP/SCP
        #for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                sshs = self.start_ssh_session()
                sshs.wait_for(self.prompt)
                sshs.sendline('echo')
                sshs.rs.start_scp()

    def test_copy_and_open_via_scp(self):
        for client in sorted(['LibSSH2']): #Remove when libssh implements nonblocking SFTP/SCP
        #for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                test_name = 'test_copy_and_open_via_scp'
                remote_path = os.path.join(self.remote_dir,test_name)
                sshs = self.start_ssh_session()
                sshs.rs.start_scp()
                sshs.rs.scp.put_folder(self.test_dir,remote_path)

    def test_file_operations_via_scp(self):
        for client in sorted(['LibSSH2']): #Remove when libssh implements nonblocking SFTP/SCP
        #for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                test_name = 'test_file_operations_via_scp'
                remote_path = os.path.join(self.remote_dir,test_name)
                sshs = self.start_ssh_session(test_name)
                sshs.rs.start_scp()
                sshs.rs.scp.put_folder(self.test_dir,remote_path)
                def test_path(path):
                    data = sshs.rs.scp.read(path,iter=False)
                    assert b'THIS IS A TEST' in data
                    del data
                    file_data = b''
                    iter = sshs.rs.scp.read(path)
                    for data in iter:
                        file_data+=data
                    assert b'THIS IS A TEST' in file_data
                    del file_data
                files_path = os.path.join(remote_path,'file_tests')
                paths = [
                    os.path.join(remote_path,'test_scp.py'),
                    os.path.join(files_path,'a'),
                    os.path.join(files_path,os.path.join('test_dir','b'))
                ]
                for path in paths:
                    test_path(path)

    def test_ignore_existing_dirs_via_scp(self):
        for client in sorted(['LibSSH2']): #Remove when libssh implements nonblocking SFTP/SCP
        #for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                test_name = 'test_ignore_existing_dirs_via_scp'
                remote_path = os.path.join(self.remote_dir,test_name)
                failed = False
                sshs = self.start_ssh_session(test_name)
                sshs.rs.start_scp()
                sshs.rs.scp.ignore_existing_dirs = False
                try:
                    sshs.rs.scp.put_folder(self.test_dir,remote_path)
                    sshs.rs.scp.put_folder(self.test_dir,remote_path)
                except:
                    failed = True
                assert failed==False

if __name__ == '__main__':
    unittest.main()
