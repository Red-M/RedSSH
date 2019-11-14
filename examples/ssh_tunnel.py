#!/usr/bin/env python3
import requests # This requires the socks supported requests package,
# installable via `pip install requests[socks]`.
import redssh
import getpass

def main():
    username = input('Username: ')
    hostname = input('Hostname: ')
    passwd = getpass.getpass()
    rs = redssh.RedSSH()

    test_string = '<title>Error 404 (Not Found)!!1</title>'
    target_host = 'google.com'

    print(hostname)
    rs.connect(hostname=hostname,username=username,password=passwd,allow_agent=True,timeout=1.5)

    (local_tun_thread,local_thread_terminate,local_tun_server,local_port) = rs.local_tunnel(0,target_host,80)
    rs.remote_tunnel(2223,target_host,80)
    (dyn_tun_thread,dyn_thread_terminate,dyn_tun_server,dyn_port) = rs.dynamic_tunnel(0)
    proxies = {'http':'socks5://localhost:'+str(dyn_port),'https':'socks5://localhost:'+str(dyn_port)}
    local = requests.get('http://localhost:'+str(local_port)).text
    remote = 'curl: '+rs.command('curl http://localhost:2223/')
    dynamic = requests.get('http://'+target_host,headers={'host':'localhost'},proxies=proxies).text

    print('Local: '+str(test_string in local))
    print('Remote: '+str(test_string in remote))
    print('Dynamic: '+str(test_string in dynamic))

    rs.exit() # it is polite to properly exit the session, but you don't have to.


if __name__=='__main__':
    main()

