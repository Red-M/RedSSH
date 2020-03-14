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

    def test_remove_and_rename_file_operations_via_sftp(self):
        test_name = 'test_remove_and_rename_file_operations_via_sftp'
        remote_path = os.path.join(self.remote_dir,test_name)
        sshs = self.start_ssh_session(test_name)
        sshs.rs.start_sftp()
        sshs.rs.sftp.put_folder(self.test_dir,remote_path)
        dir_to_test = os.path.join(os.path.join(remote_path,'file_tests'),'c')
        file_to_rename = os.path.join(os.path.join(remote_path,'file_tests'),'a')
        renamed = os.path.join(os.path.join(remote_path,'file_tests'),'b')
        sshs.rs.sftp.rename(file_to_rename,renamed)
        sshs.rs.sftp.mkdir(dir_to_test)
        sshs.rs.sftp.rmdir(dir_to_test)

    def test_symblink_file_operations_via_sftp(self):
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
        test_name = 'test_stat_file_operations_via_sftp'
        remote_path = os.path.join(self.remote_dir,test_name)
        sshs = self.start_ssh_session(test_name)
        sshs.rs.start_sftp()
        sshs.rs.sftp.put_folder(self.test_dir,remote_path)
        file_to_stat = os.path.join(os.path.join(remote_path,'file_tests'),'a')
        sshs.rs.sftp.stat(file_to_stat)
        sshs.rs.sftp.setstat(file_to_stat,oct(700))
        sshs.rs.sftp.stat(file_to_stat)
        sshs.rs.sftp.statvfs(file_to_stat)

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


    def test_file_open_via_sftpfile(self):
        test_name = 'test_file_open_via_sftpfile'
        remote_path = os.path.join(self.remote_dir,test_name)
        sshs = self.start_ssh_session(test_name)
        sshs.rs.start_sftp()
        sshs.rs.sftp.put_folder(self.test_dir,remote_path)
        file_to_stat = os.path.join(remote_path,'test_sftp.py')
        f = sshs.rs.sftp.open(file_to_stat,redssh.libssh2.LIBSSH2_FXF_READ,redssh.libssh2.LIBSSH2_SFTP_S_IRUSR,True)
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

