import pytest
import socket
import unittest
import threading
import multiprocessing
import requests
import redssh
import time

from .base_test import base_test as unittest_base


def get_local(url,headers={},proxies={},timeout=(3,3)):
    # try:
    out = requests.get(url,timeout=timeout,headers=headers,proxies=proxies).text
    return(out)
    # except Exception as e:
        # print(e)


class RedSSHUnitTest(unittest_base):

    def test_local_tunnel_bad_host(self):
        sshs = self.start_ssh_session()
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        sshs.wait_for(self.prompt)
        port = sshs.rs.dynamic_tunnel(0)
        failed = False
        try:
            out = get_local('http://ksmjdlfngkdsfg.com',headers={'host':'localhost'},proxies={'http':'socks5h://localhost:'+str(port),'https':'socks5h://localhost:'+str(port)})
        except:
            failed = True
        assert failed==True

    def test_local_tunnel_error_levels(self):
        sshs = self.start_ssh_session()
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        sshs.wait_for(self.prompt)
        for error_level in redssh.enums.TunnelErrorLevel:
            port = sshs.rs.local_tunnel(0,self.remote_tunnel_hostname,self.remote_tunnel_bad_port,error_level=error_level)
            try:
                get_local('http://localhost:'+str(port),timeout=(0.5,0.5))
            except:
                pass
            sshs.rs.close_tunnels()

    # def test_remote_tunnel_error_levels(self):
        # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # sock.bind(('localhost', 0))
        # rem_port = int(sock.getsockname()[1])
        # sock.close()

        # sshs = self.start_ssh_session()
        # sshs.wait_for(self.prompt)
        # sshs.sendline('echo')
        # sshs.wait_for(self.prompt)
        # for error_level in redssh.enums.TunnelErrorLevel:
            # print(error_level)
            # if not error_level==
            # sshs.rs.remote_tunnel(rem_port,self.remote_tunnel_hostname,self.remote_tunnel_bad_port,error_level=error_level)
            # try:
                # get_local('http://localhost:'+str(rem_port),timeout=(0.5,0.5))
            # except:
                # pass
            # sshs.rs.close_tunnels()

    # @pytest.mark.xfail
    def test_local_tunnel_read_write(self):
        sshs = self.start_ssh_session()
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        sshs.wait_for(self.prompt)
        port = sshs.rs.local_tunnel(0,self.remote_tunnel_hostname,self.remote_tunnel_port,error_level=self.error_level)
        out = get_local('http://localhost:'+str(port))
        assert self.response_text in out
        assert sshs.rs.tunnel_is_alive(redssh.enums.TunnelType.local,port,self.remote_tunnel_hostname,self.remote_tunnel_port)

    # @pytest.mark.xfail
    def test_dynamic_tunnel_read_write(self):
        sshs = self.start_ssh_session(class_init={'auto_terminate_tunnels':True})
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        sshs.wait_for(self.prompt)
        port = sshs.rs.dynamic_tunnel(0,error_level=self.error_level)
        out = get_local('http://google.com',headers={'host':'localhost'},proxies={'http':'socks5://localhost:'+str(port),'https':'socks5://localhost:'+str(port)})
        assert self.response_text in out

    # @pytest.mark.xfail
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
        sshs.rs.remote_tunnel(rem_port,self.remote_tunnel_hostname,self.remote_tunnel_port,error_level=self.error_level)
        out = get_local('http://localhost:'+str(rem_port))
        assert self.response_text in out

    # @pytest.mark.xfail
    def test_nodelay_local_remote_dynamic_tunnels(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.bind(('localhost', 0))
        rem_port = int(sock.getsockname()[1])
        sock.close()

        sshs = self.start_ssh_session(class_init={'tcp_nodelay':True})
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        sshs.wait_for(self.prompt)

        sshs.rs.remote_tunnel(rem_port,self.remote_tunnel_hostname,self.remote_tunnel_port,error_level=self.error_level)
        out = get_local('http://localhost:'+str(rem_port))
        assert self.response_text in out

        local_port = sshs.rs.local_tunnel(0,self.remote_tunnel_hostname,self.remote_tunnel_port,error_level=self.error_level)
        out = get_local('http://localhost:'+str(local_port))
        assert self.response_text in out

        dyn_port = sshs.rs.dynamic_tunnel(0,error_level=self.error_level)
        out = get_local('http://google.com',headers={'host':'localhost'},proxies={'http':'socks5://localhost:'+str(dyn_port),'https':'socks5://localhost:'+str(dyn_port)})
        assert self.response_text in out

        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.local,local_port,self.remote_tunnel_hostname,self.remote_tunnel_port)
        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.remote,rem_port,self.remote_tunnel_hostname,self.remote_tunnel_port)
        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.dynamic,dyn_port)
        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.local,dyn_port)

    # @pytest.mark.xfail
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

        sshs.rs.remote_tunnel(rem_port,self.remote_tunnel_hostname,self.remote_tunnel_port,error_level=self.error_level)
        out = get_local('http://localhost:'+str(rem_port))
        assert self.response_text in out

        local_port = sshs.rs.local_tunnel(0,self.remote_tunnel_hostname,self.remote_tunnel_port,error_level=self.error_level)
        out = get_local('http://localhost:'+str(local_port))
        assert self.response_text in out

        dyn_port = sshs.rs.dynamic_tunnel(0,error_level=self.error_level)
        out = get_local('http://google.com',headers={'host':'localhost'},proxies={'http':'socks5://localhost:'+str(dyn_port),'https':'socks5://localhost:'+str(dyn_port)})
        assert self.response_text in out

        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.local,local_port,self.remote_tunnel_hostname,self.remote_tunnel_port)
        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.remote,rem_port,self.remote_tunnel_hostname,self.remote_tunnel_port)
        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.dynamic,dyn_port)
        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.local,dyn_port)

    # @pytest.mark.xfail
    def test_auto_terminate_tunnels(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('localhost', 0))
        rem_port = int(sock.getsockname()[1])
        sock.close()

        sshs = self.start_ssh_session(class_init={'auto_terminate_tunnels':True})
        sshs.wait_for(self.prompt)
        sshs.sendline('echo')
        sshs.wait_for(self.prompt)

        sshs.rs.remote_tunnel(rem_port,self.remote_tunnel_hostname,self.remote_tunnel_port,error_level=self.error_level)
        out = get_local('http://localhost:'+str(rem_port))
        assert self.response_text in out

        local_port = sshs.rs.local_tunnel(0,self.remote_tunnel_hostname,self.remote_tunnel_port,error_level=self.error_level)
        out = get_local('http://localhost:'+str(local_port))
        assert self.response_text in out

        dyn_port = sshs.rs.dynamic_tunnel(0,error_level=self.error_level)
        out = get_local('http://google.com',headers={'host':'localhost'},proxies={'http':'socks5://localhost:'+str(dyn_port),'https':'socks5://localhost:'+str(dyn_port)})
        assert self.response_text in out

        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.local,local_port,self.remote_tunnel_hostname,self.remote_tunnel_port)
        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.remote,rem_port,self.remote_tunnel_hostname,self.remote_tunnel_port)
        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.dynamic,dyn_port)
        sshs.rs.shutdown_tunnel(redssh.enums.TunnelType.local,dyn_port)


if __name__ == '__main__':
    unittest.main()

