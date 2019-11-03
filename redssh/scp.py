import os
import time
import re

from redssh import libssh2
from redssh import exceptions

DEFAULT_WRITE_MODE = libssh2.LIBSSH2_FXF_WRITE|libssh2.LIBSSH2_FXF_CREAT|libssh2.LIBSSH2_FXF_TRUNC
DEFAULT_FILE_MODE = libssh2.LIBSSH2_SFTP_S_IRUSR | libssh2.LIBSSH2_SFTP_S_IWUSR | libssh2.LIBSSH2_SFTP_S_IRGRP | libssh2.LIBSSH2_SFTP_S_IWGRP | libssh2.LIBSSH2_SFTP_S_IROTH

class RedSCP(object):
    def __init__(self,caller):
        self.caller = caller


    def _exec(self, command):
        out = b''
        channel = self.caller._block(self.caller.session.open_session)
        if self.caller.request_pty==True:
            self.caller._block(channel.pty)
        self.caller._block(channel.execute,command)
        iter = self.caller._read_iter(channel.read,True)
        for data in iter:
            out+=data
        self.caller._block(channel.wait_eof)
        self.caller._block(channel.close)
        ret = self.caller._block(channel.get_exit_status)
        # (ret,sig,errmsg,lang) = self.caller._block(channel.get_exit_signal)
        return(ret,out)


    def mkdir(self,remote_path,dir_mode):
        '''
        Makes a directory using SCP on the remote server.

        .. warning::
            This will only create directories with the user you logged in as, not the current user you are running commands as.

        :param remote_path: Path the directory is going to be made at on the remote server.
        :type remote_path: ``str``
        :param dir_mode: File mode in decimal (not the octal value) for the directory being created.
        :type dir_mode: ``int``
        :return: ``None``
        '''
        self._exec('mkdir -p '+remote_path)
        self._exec('chmod '+oct(dir_mode)[3:]+' '+remote_path)

    def list_dir(self,remote_path):
        '''
        List a directory or path on the remote server.

        .. warning::
            This will only open files with the user you logged in as, not the current user you are running commands as.

        :param remote_path: Path to list on the remote server.
        :type remote_path: ``str``
        :return: ``dict`
        '''
        out = {'dirs':[],'files':[]}
        (ret,cmd_out) = self._exec('stat '+remote_path)
        if ret==0:
            out['dirs'] = cmd_out
        return(out)

    def write(self,local_path,remote_path):
        '''
        Write a local file to a remote file path over SCP on the remote server.

        .. warning::
            This will only write files with the user you logged in as, not the current user you are running commands as.

        :param local_path: Local path to read from.
        :type local_path: ``str``
        :param remote_path: Remote path to write to.
        :type remote_path: ``str``
        :return: ``None``
        '''
        # print(remote_path)
        stat = os.stat(local_path)
        f = open(local_path,'rb',2097152)
        chan = self.caller._block(self.caller.session.scp_send64,remote_path,stat.st_mode & 0o777,stat.st_size,stat.st_mtime,stat.st_atime)
        for data in f:
            self.caller._block_write(chan.write,data)
        self.caller._block(chan.send_eof)
        self.caller._block(chan.close)

    def read(self,file_path,iter=True):
        '''
        Read from file over SCP on the remote server.

        .. warning::
            This will only read files with the user you logged in as, not the current user you are running commands as.

        :param file_path: Remote file path to read from.
        :type file_path: ``str``
        :return: ``byte str`` or ``iter``
        '''
        (chan,file_info) = self.caller._block(self.caller.session.scp_recv2,file_path)
        if iter==True:
            return(self.caller._read_iter(chan.read,True))
        elif iter==False:
            data = b''
            iter = self.caller._read_iter(chan.read,True)
            for chunk in iter:
                data+=chunk
            return(data)

    def put_folder(self,local_path,remote_path,recursive=False):
        '''
        Upload an entire folder via SCP to the remote session. Similar to ``scp /files/* user@host:/target``
        Also retains file permissions.

        .. warning::
            This will only upload with the user you logged in as, not the current user you are running commands as.

        :param local_path: The local path, on the machine where your code is running from, to upload from.
        :type local_path: ``str``
        :param remote_path: The remote path to upload the ``local_path`` to.
        :type remote_path: ``str``
        :param recursive: Enable recursion down multiple directories from the top level of ``local_path``.
        :type recursive: ``bool``
        '''
        for (dirpath,dirnames,filenames) in os.walk(local_path):
            for dirname in dirnames:
                local_dir_path = os.path.join(local_path,dirname)
                remote_dir_path = os.path.join(remote_path,dirname)
                if not dirname.encode('utf8') in self.list_dir(remote_path)['dirs']:
                    self.mkdir(remote_dir_path,os.stat(local_dir_path).st_mode)
                if recursive==True:
                    self.put_folder(local_dir_path,remote_dir_path,recursive=recursive)
            for filename in filenames:
                local_file_path = os.path.join(dirpath,filename)
                remote_file_base = local_file_path[len(local_path):0-len(filename)]
                if remote_file_base.startswith('/'):
                    remote_file_base = remote_file_base[1:]
                remote_file_path = os.path.join(os.path.join(remote_path,remote_file_base),filename)
                self.put_file(local_file_path,remote_file_path)

    def put_file(self,local_path,remote_path):
        '''
        Upload file via SCP to the remote session. Similar to ``scp /files/file user@host:/target``.
        Also retains file permissions.

        .. warning::
            This will only upload with the user you logged in as, not the current user you are running commands as.

        :param local_path: The local path to upload from.
        :type local_path: ``str``
        :param remote_path: The remote path to upload the ``local_path`` to.
        :type remote_path: ``str``
        '''
        self.write(local_path,remote_path)
