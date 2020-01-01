import unittest
import pwd
import os
import sys
import socket
import shutil
import redssh

from .embedded_server.openssh import OpenSSHServer


PKEY_FILENAME = os.path.sep.join([os.path.dirname(__file__), 'unit_test_key'])
PUB_FILE = "%s.pub" % (PKEY_FILENAME,)



class SSHSession(object):
    def __init__(self,hostname='127.0.0.1',port=2200,class_init={},connect_args={}):
        self.rs = redssh.RedSSH(**class_init)
        self.rs.connect(hostname, port, **connect_args)

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

class base_test(unittest.TestCase):
    def setUp(self):
        self.username = pwd.getpwuid(os.geteuid()).pw_name
        self.prompt = '$ '
        if self.username=='root':
            self.prompt = '# '
        self.key_path = os.path.join(os.path.join(os.getcwd(),'tests'),'ssh_host_key')
        self.key_pub_path = self.key_path+'.pub'
        self.bad_key_path = os.path.join(os.path.join(os.getcwd(),'tests'),'ssh_host_does_not_exist')
        self.ssh_servers = []
        self.ssh_sessions = []
        self.server_hostname = '127.0.0.1'
        _mask = int('0600') if sys.version_info <= (2,) else 0o600
        os.chmod(self.key_path, _mask)
        self.response_text = '<title>Error 404 (Not Found)!!1</title>'
        self.cur_dir = os.path.expanduser(os.path.dirname(__file__))
        # self.test_dir = os.path.join(self.cur_dir,'file_tests')
        self.test_dir = self.cur_dir
        test_dir = os.path.join('test_dir','sftp')
        self.remote_dir = test_dir
        self.real_remote_dir = os.path.sep+os.path.join('tmp',test_dir)
        self.remote_dir = self.real_remote_dir
        try:
            os.makedirs(self.real_remote_dir)
        except:
            pass

    def start_ssh_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('127.0.0.1', 0))
        server_port = sock.getsockname()[1]
        sock.close()
        server = OpenSSHServer(port=server_port,server_key=self.key_path)
        server.start_server()
        self.ssh_servers.append(server)
        return(server_port)

    def start_ssh_session(self,test_name=None,server_port=None,class_init={},connect_args={}):
        if isinstance(test_name,type('')):
            try:
                os.makedirs(os.path.join(self.real_remote_dir,test_name))
            except:
                pass
        if server_port==None:
            server_port = self.start_ssh_server()

        conn_args = {
            'key_filepath':self.key_path,
            'username':self.username
        }

        for arg in conn_args:
            if not arg in connect_args:
                connect_args.update({arg:conn_args[arg]})
        sshs = SSHSession(self.server_hostname,server_port,class_init,connect_args)
        self.ssh_sessions.append(sshs)
        return(sshs)

    def end_ssh_session(self,sshs):
        sshs.rs.exit()

    def tearDown(self):
        for session in self.ssh_sessions:
            self.end_ssh_session(session)
        for server in self.ssh_servers:
            server.stop()
        try:
            shutil.rmtree(self.real_remote_dir)
        except:
            pass
