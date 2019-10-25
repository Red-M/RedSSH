import os
import time
import socket
import shutil
import unittest
import threading
import multiprocessing
import paramiko
import redssh

from . import paramiko_server as ssh_server


class SSHSession(object):
    def __init__(self,hostname='localhost',port=2200,class_init={},connect_args={}):
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
        self.server_hostname = 'localhost'
        self.cur_dir = os.path.expanduser(os.path.dirname(__file__))
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

    def start_ssh_session(self,server_port=None,class_init={},connect_args={}):
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
        sshs = self.start_ssh_session()
        sshs.rs.start_sftp()
        sshs.rs.sftp.put_folder(self.cur_dir,self.remote_dir,True)

    def test_file_operations_via_sftp(self):
        sshs = self.start_ssh_session()
        sshs.rs.start_sftp()
        sshs.rs.sftp.put_folder(self.cur_dir,self.remote_dir,True)
        path = os.path.join(self.remote_dir,'test_sftp.py')
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
        shutil.rmtree(self.real_remote_dir)

if __name__ == '__main__':
    unittest.main()

