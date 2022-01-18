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

    def test_open_sftp(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                sshs = self.start_ssh_session()
                sshs.wait_for(self.prompt)
                sshs.sendline('echo')
                sshs.rs.start_sftp()

    def test_remove_and_rename_file_operations_via_sftp(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                test_name = 'test_remove_and_rename_file_operations_via_sftp'
                remote_path = os.path.join(self.remote_dir,test_name)
                sshs = self.start_ssh_session(test_name)
                sshs.rs.start_sftp()
                sshs.rs.sftp.put_folder(self.test_dir,remote_path)
                dir_to_test = os.path.join(os.path.join(remote_path,'file_tests'),'c')
                file_to_rename = os.path.join(os.path.join(remote_path,'file_tests'),'a')
                renamed = os.path.join(os.path.join(remote_path,'file_tests'),'b')
                sshs.rs.sftp.rename(file_to_rename,renamed)
                sshs.rs.sftp.mkdir(dir_to_test,16877)
                sshs.rs.sftp.rmdir(dir_to_test)
                self.tearDown()
                self.setUp()

    def test_symblink_file_operations_via_sftp(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                test_name = 'test_symblink_file_operations_via_sftp'
                remote_path = os.path.join(self.remote_dir,test_name)
                sshs = self.start_ssh_session(test_name)
                sshs.rs.start_sftp()
                sshs.rs.sftp.put_folder(self.test_dir,remote_path)
                file_to_smblink = os.path.join(os.path.join(remote_path,'file_tests'),'a')
                target = os.path.join(os.path.join(remote_path,'file_tests'),'b')
                sshs.rs.sftp.symlink(file_to_smblink,target)
                sshs.rs.sftp.lstat(file_to_smblink)
                sshs.rs.sftp.unlink(target)

    def test_stat_file_operations_via_sftp(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                test_name = 'test_stat_file_operations_via_sftp'
                remote_path = os.path.join(self.remote_dir,test_name)
                sshs = self.start_ssh_session(test_name)
                sshs.rs.start_sftp()
                sshs.rs.sftp.put_folder(self.test_dir,remote_path)
                file_to_stat = os.path.join(os.path.join(remote_path,'file_tests'),'a')
                attrs = sshs.rs.sftp.stat(file_to_stat)
                sshs.rs.sftp.setstat(file_to_stat,attrs)
                sshs.rs.sftp.stat(file_to_stat)
                sshs.rs.sftp.statvfs(file_to_stat)
                fs = sshs.rs.sftp.open(file_to_stat,sshs.rs.client.enums.SFTP.DEFAULT_READ_MODE,sshs.rs.client.enums.SFTP.DEFAULT_FILE_MODE,True)
                attrs = fs.fstat()
                try:
                    fs.fsetstat(attrs)
                except redssh.libssh2.exceptions.SFTPProtocolError:
                    pass # needs further debugging into why that error comes up.
                fs.fstatvfs()
                fs.fsync()

    def test_list_dir_via_sftp(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                test_name = 'test_list_dir_via_sftp'
                remote_path = os.path.join(self.remote_dir,test_name)
                sshs = self.start_ssh_session(test_name)
                sshs.rs.start_sftp()
                sshs.rs.sftp.put_folder(self.test_dir,remote_path)
                dir_to_list = os.path.join(remote_path,'file_tests')
                for remove in [True,False]:
                    dir_list = sshs.rs.sftp.list_dir(dir_to_list,remove)
                    for item in dir_list:
                        if client=='LibSSH2':
                            if remove==True:
                                assert item[0]!=sshs.rs.client.enums.Client.eagain.value and item[0]>0
                            elif remove==False:
                                assert item[0]==sshs.rs.client.enums.Client.eagain.value or item[0]>0
                        if client=='LibSSH':
                            if remove==True:
                                assert item[0]!=sshs.rs.client.enums.Client.eagain.value and len(item[0])>0
                            elif remove==False:
                                assert item[0]==sshs.rs.client.enums.Client.eagain.value or len(item[0])>0

    def test_copy_and_open_via_sftp(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                test_name = 'test_copy_and_open_via_sftp'
                remote_path = os.path.join(self.remote_dir,test_name)
                sshs = self.start_ssh_session(test_name)
                sshs.rs.start_sftp()
                sshs.rs.sftp.put_folder(self.test_dir,remote_path)

    def test_file_operations_via_sftp(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                test_name = 'test_file_operations_via_sftp'
                remote_path = os.path.join(self.remote_dir,test_name)
                sshs = self.start_ssh_session(test_name)
                sshs.rs.start_sftp()
                sshs.rs.sftp.put_folder(self.test_dir,remote_path)
                def test_path(path):
                    sftp_f = sshs.rs.sftp.open(path,sshs.rs.client.enums.SFTP.DEFAULT_READ_MODE,sshs.rs.client.enums.SFTP_S.IRUSR)
                    assert b'THIS IS A TEST' in sshs.rs.sftp.read(sftp_f,iter=False)
                    sshs.rs.sftp.seek(sftp_f,0)
                    file_data = b''
                    for data in sshs.rs.sftp.read(sftp_f):
                        file_data+=data
                    assert b'THIS IS A TEST' in file_data
                    del file_data
                    sshs.rs.sftp.rewind(sftp_f) # Be kind and rewind! :)
                    sshs.rs.sftp.close(sftp_f)
                files_path = os.path.join(remote_path,'file_tests')
                paths = [
                    os.path.join(remote_path,'test_sftp.py'),
                    os.path.join(files_path,'a'),
                    os.path.join(files_path,os.path.join('test_dir','b'))
                ]
                for path in paths:
                    test_path(path)

    def test_ignore_existing_dirs_via_sftp(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                test_name = 'test_ignore_existing_dirs_via_sftp'
                remote_path = os.path.join(self.remote_dir,test_name)
                failed = False
                sshs = self.start_ssh_session(test_name)
                sshs.rs.start_sftp()
                sshs.rs.sftp.ignore_existing_dirs = False
                try:
                    sshs.rs.sftp.put_folder(self.test_dir,remote_path)
                    sshs.rs.sftp.put_folder(self.test_dir,remote_path)
                except:
                    failed = True
                assert failed==True

    def test_file_open_via_sftpfile(self):
        for client in sorted(redssh.clients.enabled_clients):
            with self.subTest(client=client):
                redssh.clients.default_client = client
                test_name = 'test_file_open_via_sftpfile'
                remote_path = os.path.join(self.remote_dir,test_name)
                sshs = self.start_ssh_session(test_name)
                sshs.rs.start_sftp()
                sshs.rs.sftp.put_folder(self.test_dir,remote_path)
                file_path = os.path.join(remote_path,'test_sftp.py')
                f = sshs.rs.sftp.open(file_path,sshs.rs.client.enums.SFTP.DEFAULT_READ_MODE,sshs.rs.client.enums.SFTP_S.IRUSR,True)
                f.close()
                f.open()
                assert b'THIS IS A TEST' in f.read(iter=False)
                f.seek(0)
                file_data = b''
                for data in f.read():
                    file_data+=data
                assert b'THIS IS A TEST' in file_data
                del file_data
                f.rewind()


if __name__ == '__main__':
    unittest.main()

