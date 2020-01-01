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
        sshs = self.start_ssh_session()
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        sshs.rs.start_sftp()

    def test_copy_and_open_via_sftp(self):
        test_name = 'test_copy_and_open_via_sftp'
        remote_path = os.path.join(self.remote_dir,test_name)
        sshs = self.start_ssh_session(test_name)
        sshs.rs.start_sftp()
        sshs.rs.sftp.put_folder(self.test_dir,remote_path)

    def test_file_operations_via_sftp(self):
        test_name = 'test_file_operations_via_sftp'
        remote_path = os.path.join(self.remote_dir,test_name)
        sshs = self.start_ssh_session(test_name)
        sshs.rs.start_sftp()
        sshs.rs.sftp.put_folder(self.test_dir,remote_path)
        def test_path(path):
            sftp_f = sshs.rs.sftp.open(path,redssh.libssh2.LIBSSH2_FXF_READ,redssh.libssh2.LIBSSH2_SFTP_S_IRUSR)
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


if __name__ == '__main__':
    unittest.main()

