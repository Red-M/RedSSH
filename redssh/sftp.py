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

class RedSFTP(object):
    def __init__(self,caller):
        self.caller = caller
        self.enable_fsync = False
        self.client = self.caller._block(self.caller.session.sftp_init)


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
        if self.caller.__check_for_attr__('sftp'):
            self.caller._block(self.client.mkdir,remote_path,dir_mode)

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
        if self.caller.__check_for_attr__('sftp'):
            return(self.caller._block(self.client.opendir,remote_path))

    def open(self,remote_path,sftp_flags,file_mode):
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
        if self.caller.__check_for_attr__('sftp'):
            return(self.caller._block(self.client.open,remote_path,sftp_flags,file_mode))

    def rewind(self,file_obj):
        '''
        Rewind a file object over SFTP to the beginning.

        :param file_obj: `ssh2.sftp.SFTPHandle` to interact with.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        :return: ``None``
        '''
        if self.caller.__check_for_attr__('sftp'):
            self.caller._block(file_obj.rewind)

    def seek(self,file_obj,offset):
        '''
        Seek to a certain location in a file object over SFTP.

        :param file_obj: `ssh2.sftp.SFTPHandle` to interact with.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        :param offset: What location to seek to in the file.
        :type offset: ``int``
        :return: ``None``
        '''
        if self.caller.__check_for_attr__('sftp'):
            self.caller._block(file_obj.seek64,offset)

    def write(self,file_obj,data_bytes):
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
        if self.caller.__check_for_attr__('sftp'):
            self.caller._block_write(file_obj.write,data_bytes)

    def read(self,file_obj,iter=False):
        '''
        Read from file object over SFTP on the remote server.

        .. warning::
            This will only read files with the user you logged in as, not the current user you are running commands as.

        :param file_obj: `ssh2.sftp.SFTPHandle` to interact with.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        :param iter: Flag for if you want the iterable object instead of just a byte string returned.
        :type iter: ``bool``
        :return: ``byte str`` or ``iter``
        '''
        if self.caller.__check_for_attr__('sftp'):
            if iter==True:
                return(self.caller._read_iter(file_obj.read))
            elif iter==False:
                data = b''
                iter = self.caller._read_iter(file_obj.read)
                for chunk in iter:
                    data+=chunk
                return(data)

    def close(self,file_obj):
        '''
        Closes a file object over SFTP on the remote server. It is a good idea to delete the ``file_obj`` after calling this.

        .. warning::
            This will only close files with the user you logged in as, not the current user you are running commands as.

        :param file_obj: `ssh2.sftp.SFTPHandle` to interact with.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        :return: ``None``
        '''
        if self.caller.__check_for_attr__('sftp'):
            if self.enable_fsync==True:
                self.caller._block(file_obj.fsync)
            self.caller._block(file_obj.close)

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
        if self.caller.__check_for_attr__('sftp'):
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
        if self.caller.__check_for_attr__('sftp'):
            f = self.open(remote_path,libssh2.LIBSSH2_FXF_WRITE|libssh2.LIBSSH2_FXF_CREAT|libssh2.LIBSSH2_FXF_TRUNC,os.stat(local_path).st_mode)
            self.write(f,open(local_path,'rb').read())
            self.close(f)


