import pytest
import socket
import unittest
import threading
import multiprocessing
import requests
import redssh
import time

from .base_test import base_test as unittest_base


def get_local(url,headers={},proxies={}):
    try:
        out = requests.get(url,timeout=(3,3),headers=headers,proxies=proxies).text
        return(out)
    except Exception as e:
        print(e)


class RedSSHUnitTest(unittest_base):

    def test_local_tunnel_bad_host(self):
        try:
            sshs = self.start_ssh_session()
            sshs.wait_for(self.prompt)
            sshs.sendline('echo')
            sshs.wait_for(self.prompt)
            port = sshs.rs.dynamic_tunnel(0)
            # out = get_local('http://ksmjdlfngkdsfg.com',headers={'host':'localhost'},proxies={'http':'socks5h://localhost:'+str(port),'https':'socks5h://localhost:'+str(port)})
        except:
            pass

    def test_local_tunnel_read_write(self):
        sshs = self.start_ssh_session()
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        sshs.wait_for(self.prompt)
        port = sshs.rs.local_tunnel(0,'google.com',80)
        out = get_local('http://localhost:'+str(port))
        assert self.response_text in out

    def test_dynamic_tunnel_read_write(self):
        sshs = self.start_ssh_session()
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        sshs.wait_for(self.prompt)
        port = sshs.rs.dynamic_tunnel(0)
        out = get_local('http://google.com',headers={'host':'localhost'},proxies={'http':'socks5://localhost:'+str(port),'https':'socks5://localhost:'+str(port)})
        assert self.response_text in out

    @pytest.mark.xfail
    def test_remote_tunnel_read_write(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('localhost', 0))
        rem_port = int(sock.getsockname()[1])
        sock.close()

        sshs = self.start_ssh_session()
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        sshs.wait_for(self.prompt)
        sshs.rs.remote_tunnel(rem_port,'google.com',80)
        out = get_local('http://localhost:'+str(rem_port))
        assert self.response_text in out

    @pytest.mark.xfail
    def test_local_remote_dynamic_tunnels(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('localhost', 0))
        rem_port = int(sock.getsockname()[1])
        sock.close()

        sshs = self.start_ssh_session()
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        sshs.wait_for(self.prompt)
        sshs.rs.remote_tunnel(rem_port,'google.com',80)
        out = get_local('http://localhost:'+str(rem_port))
        assert self.response_text in out

        local_port = sshs.rs.local_tunnel(0,'google.com',80)
        out = get_local('http://localhost:'+str(local_port))
        assert self.response_text in out

        dyn_port = sshs.rs.dynamic_tunnel(0)
        out = get_local('http://google.com',headers={'host':'localhost'},proxies={'http':'socks5://localhost:'+str(dyn_port),'https':'socks5://localhost:'+str(dyn_port)})
        assert self.response_text in out

        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.local,local_port,'google.com',80)
        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.remote,rem_port,'google.com',80)
        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.dynamic,dyn_port)
        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.local,dyn_port)


if __name__ == '__main__':
    unittest.main()

