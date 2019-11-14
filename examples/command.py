#!/usr/bin/env python3
import redssh
import getpass

def wait_for(rs, wait_string):
    if isinstance(wait_string,type('')):
        wait_string = wait_string.encode('utf8')
    read_data = b''
    while not wait_string in read_data:
        for data in rs.read():
            read_data += data
    return(read_data)

def sendline(rs, line):
    rs.send(line+'\r\n')

def main():
    username = input('Username: ')
    hostname = input('Hostname: ')
    passwd = getpass.getpass()

    rs = redssh.RedSSH()
    print(hostname)
    rs.connect(hostname=hostname,username=username,password=passwd,allow_agent=True,timeout=1.5)

    wait_for(rs, '$')
    sendline(rs,'unset HISTFILE;whoami\r\n')
    print(wait_for(rs, '$'))

    rs.exit()


if __name__=='__main__':
    main()
