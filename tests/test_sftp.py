import os
import time
import socket
import shutil
import unittest
import threading
import multiprocessing
import paramiko
import redssh

from .servers import paramiko_server as ssh_server


class SSHSession(object):
    def __init__(self,hostname='127.0.0.1',port=2200,class_init={},connect_args={}):
        self.rs = redssh.RedSSH(**class_init)
        self.rs.connect(hostname, port, 'redm', 'foobar!',**connect_args)

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
        self.ssh_servers = []
        self.ssh_sessions = []
        self.server_hostname = '127.0.0.1'
        self.cur_dir = os.path.expanduser(os.path.dirname(__file__))
        # self.test_dir = os.path.join(self.cur_dir,'file_tests')
        self.test_dir = self.cur_dir
        test_dir = os.path.join('test_dir','sftp')
        self.remote_dir = test_dir
        self.real_remote_dir = os.path.sep+os.path.join('tmp',test_dir)
        try:
            os.makedirs(self.real_remote_dir)
        except:
            pass

    def start_ssh_server(self):
        q = multiprocessing.Queue()
        server = multiprocessing.Process(target=ssh_server.start_server,args=(q,))
        server.start()
        self.ssh_servers.append(server)
        server_port = q.get()
        return(server_port)

    def start_ssh_session(self,test_name=None,server_port=None,class_init={},connect_args={}):
        if isinstance(test_name,type('')):
            try:
                os.makedirs(os.path.join(self.real_remote_dir,test_name))
            except:
                pass
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
        try:
            shutil.rmtree(self.real_remote_dir)
        except:
            pass



    def test_open_sftp(self):
        sshs = self.start_ssh_session()
        sshs.wait_for('Command$ ')
        sshs.sendline('reply')
        sshs.rs.start_sftp()

    def test_copy_and_open(self):
        test_name = 'copy_and_open'
        remote_path = os.path.join(self.remote_dir,test_name)
        sshs = self.start_ssh_session(test_name)
        sshs.rs.start_sftp()
        sshs.rs.sftp.put_folder(self.test_dir,remote_path)

    def test_file_operations_via_sftp(self):
        test_name = 'file_operations_via_sftp'
        remote_path = os.path.join(self.remote_dir,test_name)
        sshs = self.start_ssh_session(test_name)
        sshs.rs.start_sftp()
        sshs.rs.sftp.put_folder(self.test_dir,remote_path)
        def test_path(path):
            sftp_f = sshs.rs.sftp.open(path,redssh.libssh2.LIBSSH2_FXF_READ,redssh.libssh2.LIBSSH2_SFTP_S_IRUSR)
            assert b'THIS IS A TEST' in sshs.rs.sftp.read(sftp_f)
            sshs.rs.sftp.seek(sftp_f,0)
            file_data = b''
            for data in sshs.rs.sftp.read(sftp_f,iter=True):
                print(data)
                file_data+=data
            assert b'THIS IS A TEST' in file_data
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

    def test_ignore_existing_dirs(self):
        test_name = 'ignore_existing_dirs'
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

