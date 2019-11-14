#!/usr/bin/env python3
import redssh
import getpass

def main():
    username = input('Username: ')
    hostname = input('Hostname: ')
    passwd = getpass.getpass()

    rs = redssh.RedSSH()
    print(hostname)
    rs.connect(hostname=hostname,username=username,password=passwd,allow_agent=True,timeout=1.5)
    rs.exit()


if __name__=='__main__':
    main()
