# RedSSH
# Copyright (C) 2019  Red_M ( http://bitbucket.com/Red_M )

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


import os

from redssh import libssh2
from redssh import exceptions

DEFAULT_WRITE_MODE = libssh2.LIBSSH2_FXF_WRITE|libssh2.LIBSSH2_FXF_CREAT|libssh2.LIBSSH2_FXF_TRUNC
DEFAULT_FILE_MODE = libssh2.LIBSSH2_SFTP_S_IRUSR | libssh2.LIBSSH2_SFTP_S_IWUSR | libssh2.LIBSSH2_SFTP_S_IRGRP | libssh2.LIBSSH2_SFTP_S_IWGRP | libssh2.LIBSSH2_SFTP_S_IROTH

class RedSCP(object):
    def __init__(self,caller):
        self.caller = caller


    def mkdir(self,remote_path,dir_mode):
        '''
        Makes a directory using SFTP on the remote server.

        .. warning::
            This will only create directories with the user you logged in as, not the current user you are running commands as.

        :param remote_path: Path the directory is going to be made at on the remote server.
        :type remote_path: ``str``
        :param dir_mode: File mode for the directory being created.
        :type dir_mode: ``int``
        :return: ``None``
        '''
        if self.caller.__check_for_attr__('scp'):
            self.caller._block(self.caller.channel.execute,'mkdir '+remote_path)
            self.caller._block(self.caller.channel.execute,'chmod '+dir_mode+' '+remote_path)

    def list_dir(self,remote_path):
        '''
        Open a file object over SFTP on the remote server.

        .. warning::
            This will only open files with the user you logged in as, not the current user you are running commands as.

        :param remote_path: Path that file is located at on the remote server.
        :type remote_path: ``str``
        :param sftp_flags: Flags for the SFTP session to understand what you are going to do with the file.
        :type sftp_flags: ``int``
        :param file_mode: File mode for the file being opened.
        :type file_mode: ``int``
        :return: `ssh2.sftp.SFTPHandle`
        '''
        if self.caller.__check_for_attr__('scp'):
            (chan,file_info) = self.caller._block(self.caller.session.scp_recv2,remote_path)
            print(chan)
            print(file_info)
            return(self.caller._block(self.caller.channel.execute,'ls '+remote_path))

    def write(self,file_path,file_mode,data_bytes):
        '''
        Write to a file object over SFTP on the remote server.

        .. warning::
            This will only write files with the user you logged in as, not the current user you are running commands as.

        :param file_obj: `ssh2.sftp.SFTPHandle` to interact with.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        :param data_bytes: Bytes to write to the file with.
        :type data_bytes: ``byte str``
        :return: ``None``
        '''
        if self.caller.__check_for_attr__('scp'):
            chan = self.caller._block(self.caller.session.scp_send64,path,file_mode & 0o777,len(data_bytes))
            self.caller._block_write(chan.write,data_bytes)
            self.caller._block(chan.close)

    def read(self,file_path):
        '''
        Read from file object over SFTP on the remote server.

        .. warning::
            This will only read files with the user you logged in as, not the current user you are running commands as.

        :param file_obj: `ssh2.sftp.SFTPHandle` to interact with.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        :return: ``byte str`` or ``iter``
        '''
        if self.caller.__check_for_attr__('scp'):
            (chan,file_info) = self.caller._block(self.caller.session.scp_recv2,file_path)
            if iter==True:
                return(self.caller._block(chan.read))
            elif iter==False:
                data = b''
                iter = self.caller._read_iter(chan.read)
                for chunk in iter:
                    data+=chunk
                return(data)

    def put_folder(self,local_path,remote_path,recursive=False):
        '''
        Upload an entire folder via SFTP to the remote session. Similar to ``cp -r /files/* /target``
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
        if self.caller.__check_for_attr__('scp'):
            for (dirpath,dirnames,filenames) in os.walk(local_path):
                for dirname in dirnames:
                    local_dir_path = os.path.join(local_path,dirname)
                    remote_dir_path = os.path.join(remote_path,dirname)
                    if not dirname in self.list_dir(remote_path).readdir():
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
        Upload file via SFTP to the remote session. Similar to ``cp /files/file /target``.
        Also retains file permissions.

        .. warning::
            This will only upload with the user you logged in as, not the current user you are running commands as.

        :param local_path: The local path, on the machine where your code is running from, to upload from.
        :type local_path: ``str``
        :param remote_path: The remote path to upload the ``local_path`` to.
        :type remote_path: ``str``
        '''
        if self.caller.__check_for_attr__('scp'):
            self.write(f,os.stat(local_path).st_mode,open(local_path,'rb').read())


