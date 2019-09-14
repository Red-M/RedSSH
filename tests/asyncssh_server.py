#!/usr/bin/env python

import os
import sys
import time
import asyncio
import asyncssh

server_port = 0 # pick one for me!
server_prompt = '$'
line_endings = '\r\n'
server_q = None


passwords = {'redm': 'foobar!'}

async def res(iter):
    async for item in iter:
        print(item)
        return(item)



class compatChan(object):
    def __init__(self, chan):
        self.chan = chan

    def send(self,line):
        return(self.chan.stdout.write(line))

    def read(self):
        pass

class Commands(object):
    def __init__(self, chan):
        global server_port,server_prompt
        self.chan = chan
        self.server_prompt = server_prompt
        self.quit = False

    def send(self, line):
        self.chan.send(line+line_endings)

    def tunnel_test(self, line):
        self.send('Tunneled')

    def cmd_reply(self):
        self.send('PONG!')

    def cmd_sudo(self):
        self.chan.send('[sudo] password for lowly_pleb: ')
        received_passwd = self.chan.read().strip('\r\n')
        self.send('')
        if received_passwd=='bar':
            self.server_prompt = '#'
        else:
            self.send('Sorry, try again.')

    def cmd_sudo_custom_sudo(self):
        self.cmd_sudo()

    def cmd_whoami(self):
        whoswho = {'$':'lowly_pleb','#':'root'}
        self.send(whoswho[self.server_prompt])

    def cmd_exit(self):
        self.send('END OF TEST')
        self.quit = True



async def handle_client(process):
    chan = compatChan(process)
    commands = Commands(chan)
    chan.send('MOTD'+line_endings)
    while not commands.quit==True:
        chan.send(line_endings+'Command'+server_prompt+' ')
        # print(dir(process.stdin.readline()))
        line = await process.stdin.readline()
        command = 'cmd_'+line.strip('\r\n').replace(' ','_')
        print('Got: '+command)
        # chan.send(line_endings)
        if command in dir(commands):
            func = getattr(commands,command)
            func()
    time.sleep(1)
    process.exit(0)


async def handle_connection(reader, writer):
    while not reader.at_eof():
        data = await reader.read(8192)

        try:
            writer.write(data)
        except:
            break

    writer.close()

class MySSHServer(asyncssh.SSHServer):
    def connection_requested(self, dest_host, dest_port, orig_host, orig_port):
        return(handle_connection)

    def connection_made(self, conn):
        print('SSH connection received from %s.' %
                  conn.get_extra_info('peername')[0])

    def connection_lost(self, exc):
        if exc:
            print('SSH connection error: ' + str(exc), file=sys.stderr)
        else:
            print('SSH connection closed.')

    def begin_auth(self, username):
        # If the user's password is the empty string, no auth is required
        return passwords.get(username) != ''

    def password_auth_supported(self):
        return True

    def validate_password(self, username, password):
        return(password==passwords.get(username, '*'))






async def start_ssh_server(q):
    global server_port,server_q
    listener = await asyncssh.create_server(MySSHServer,'',server_port,server_host_keys=['tests'+os.path.sep+'ssh_host_key'],process_factory=handle_client)
    for item in listener.sockets:
        server_q.put(item.getsockname()[1])
        break

def start_server(q):
    global server_port,server_q
    server_q = q
    try:
        loop = asyncio.get_event_loop()
    except Exception as e:
        loop = asyncio.new_event_loop()

    try:
        loop.run_until_complete(start_ssh_server(q))
    except (OSError, asyncssh.Error) as exc:
        sys.exit('SSH server failed: ' + str(exc))

    loop.run_forever()

