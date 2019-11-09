#!/usr/bin/env python3
import time
import multiprocessing

from servers import asyncssh_server as ssh_server

def main():
    q = multiprocessing.Queue()
    server = multiprocessing.Process(target=ssh_server.start_server,args=(q,))
    server.start()
    server_port = q.get()
    print(server_port)
    while True:
        time.sleep(1)

if __name__=='__main__':
    main()