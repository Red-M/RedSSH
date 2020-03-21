# RedSSH
# Copyright (C) 2018 - 2020  Red_M ( http://bitbucket.com/Red_M )

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
DEFAULT_READ_MODE = libssh2.LIBSSH2_FXF_READ
DEFAULT_FILE_MODE = libssh2.LIBSSH2_SFTP_S_IRUSR | libssh2.LIBSSH2_SFTP_S_IWUSR | libssh2.LIBSSH2_SFTP_S_IRGRP | libssh2.LIBSSH2_SFTP_S_IWGRP | libssh2.LIBSSH2_SFTP_S_IROTH

class RedSFTP(object):
    '''
    .. warning::
    This will only interact with the remote server as the user you logged in as, not the current user you are running commands as.

    Set ``self.ignore_existing_dirs`` to ``False`` to make `redssh.sftp.RedSFTP.mkdir` not ignore already existing directories.
    '''
    def __init__(self,ssh_session):
        self.ssh_session = ssh_session
        self.enable_fsync = False
        self.ignore_existing_dirs = True
        self.client = self.ssh_session._block(self.ssh_session.session.sftp_init)


    def fsetstat(self,file_obj,attrs):
        '''
        Set file stat attributes for a `ssh2.sftp.SFTPHandle` object.

        :param file_obj: `ssh2.sftp.SFTPHandle` of the file on the remote server.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        :param attrs: Attributes to set.
        :type attrs: `ssh2.sftp.SFTPAttributes`
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            return(self.ssh_session._block(file_obj.fsetstat,attrs))

    def fstat(self,file_obj):
        '''
        Get file stat attributes from a `ssh2.sftp.SFTPHandle` object.

        :param file_obj: `ssh2.sftp.SFTPHandle` of the file on the remote server.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            return(self.ssh_session._block(file_obj.fstat))

    def fstatvfs(self,file_obj):
        '''
        Get file system statistics for a `ssh2.sftp.SFTPHandle` object.

        :param file_obj: `ssh2.sftp.SFTPHandle` of the file on the remote server.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            return(self.ssh_session._block(file_obj.fstatvfs))

    def fsync(self,file_obj):
        '''
        Tells the remote file system to synchronize the file to disk.
        This will only work if the SFTP session has ``enable_fsync`` set to ``True``

        :param file_obj: `ssh2.sftp.SFTPHandle` of the file on the remote server.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        '''
        if self.ssh_session.__check_for_attr__('sftp') and self.enable_fsync==True:
            self.ssh_session._block(file_obj.fsync)

    def rmdir(self,remote_path):
        '''
        Remove directory at ``remote_path``.

        :param remote_path: Path to the directory to remove on the remote server.
        :type remote_path: ``str``
        :return: `int`
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            return(self.ssh_session._block(self.client.rmdir,remote_path))

    def rename(self,original_path,destination_path):
        '''
        Rename file at ``original_path`` to ``destination_path``.

        :param original_path: Original path on the remote server.
        :type original_path: ``str``
        :param destination_path: Destination path on the remote server.
        :type destination_path: ``str``
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            self.ssh_session._block(self.client.rename,original_path,destination_path)

    def unlink(self,remote_path):
        '''
        Delete or unlink file at ``remote_path``.

        :param remote_path: Path that file will be deleted or unlinked on the remote server.
        :type remote_path: ``str``
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            self.ssh_session._block(self.client.unlink,remote_path)

    def symlink(self,path,target):
        '''
        Creates a symbolic link at ``path`` to then link to ``target``.

        :param path: Path that the symbolic link will live at on the remote server.
        :type path: ``str``
        :param target: Path that the symbolic link at ``path`` will point to on the remote server.
        :type target: ``str``
        :return: `int`
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            return(self.ssh_session._block(self.client.symlink,path,target))

    def statvfs(self,remote_path):
        '''
        Gets file system information for ``remote_path``.

        :param remote_path: Path that the file system information is going to be queried for on the remote server.
        :type remote_path: ``str``
        :return: `ssh2.sftp_handle.SFTPStatVFS` or an ``int`` of the error code from `ssh2`
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            return(self.ssh_session._block(self.client.statvfs,remote_path))

    def lstat(self,remote_path):
        '''
        Gets file/directory file permissions for ``remote_path`` but follows symbolic links.

        :param remote_path: File/directory file permissions to get on the remote server.
        :type remote_path: ``str``
        :return: `ssh2.sftp_handle.SFTPAttributes` or `redssh.libssh2.LIBSSH2_ERROR_EAGAIN`
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            return(self.ssh_session._block(self.client.lstat,remote_path))

    def stat(self,remote_path):
        '''
        Gets file/directory file permissions for ``remote_path``.

        :param remote_path: File/directory file permissions to get on the remote server.
        :type remote_path: ``str``
        :return: `ssh2.sftp_handle.SFTPAttributes` or `redssh.libssh2.LIBSSH2_ERROR_EAGAIN`
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            return(self.ssh_session._block(self.client.stat,remote_path))

    def setstat(self,remote_path,attrs):
        '''
        Sets file/directory file permissions for ``remote_path``.

        :param remote_path: Path to make changes to on the remote server.
        :type remote_path: ``str``
        :param attrs: File mode for the ``remote_path`` given.
        :type attrs: ``int``
        :return: ``int``
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            return(self.ssh_session._block(self.client.setstat,remote_path,attrs))

    def mkdir(self,remote_path,dir_mode):
        '''
        Makes a directory using SFTP on the remote server.

        :param remote_path: Path the directory is going to be made at on the remote server.
        :type remote_path: ``str``
        :param dir_mode: File mode for the directory being created.
        :type dir_mode: ``int``
        :return: ``None``
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            try:
                self.ssh_session._block(self.client.mkdir,remote_path,dir_mode)
            except libssh2.exceptions.SFTPProtocolError as e:
                if self.ignore_existing_dirs==False:
                    raise(e)

    def list_dir(self,remote_path,remove_empty=False):
        '''
        Lists a directory over SFTP on the remote server.

        :param remote_path: Path that file is located at on the remote server.
        :type remote_path: ``str``
        :param remove_empty: Remove EAGAIN records from the generator
        :type remove_empty: ``bool``
        :return: ``generator`` of ``tuple``
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            # This is a patch for ssh2.sftp_handle.SFTPHandle.readdir*()
            # Because the ssh2-python implementation doesn't remove EAGAIN errors from the generator
            # It also does a few other things that I'd like to rework to get some performance back.
            iter = self.open_dir(remote_path).readdir()
            for item in iter:
                if len(item)==3 and remove_empty==True:
                    if not item[0]==libssh2.LIBSSH2_ERROR_EAGAIN:
                        yield(item)
                elif remove_empty==False:
                    yield(item)

    def open_dir(self,remote_path):
        '''
        Opens a directory object over SFTP on the remote server.

        :param remote_path: Path that file is located at on the remote server.
        :type remote_path: ``str``
        :return: `ssh2.sftp_handle.SFTPHandle`
        :raises: `ssh2.exceptions.SFTPHandleError` on errors opening directory.
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            return(self.ssh_session._block(self.client.opendir,remote_path))

    def open(self,remote_path,sftp_flags,file_mode,file_obj=False):
        '''
        Open a file object over SFTP on the remote server.

        :param remote_path: Path that file is located at on the remote server.
        :type remote_path: ``str``
        :param sftp_flags: Flags for the SFTP session to understand what you are going to do with the file.
        :type sftp_flags: ``int``
        :param file_mode: File mode for the file being opened.
        :type file_mode: ``int``
        :param file_obj: Return a file object instead of a `ssh2.sftp.SFTPHandle`
        :type file_obj: ``bool``
        :return: `ssh2.sftp.SFTPHandle` or `redssh.sftp.RedSFTPFile`
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            if file_obj==False:
                return(self.ssh_session._block(self.client.open,remote_path,sftp_flags,file_mode))
            elif file_obj==True:
                return(RedSFTPFile(self,remote_path,sftp_flags,file_mode))

    def rewind(self,file_obj):
        '''
        Rewind a file object over SFTP to the beginning.

        :param file_obj: `ssh2.sftp.SFTPHandle` to interact with.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        :return: ``None``
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            self.ssh_session._block(file_obj.rewind)

    def seek(self,file_obj,offset):
        '''
        Seek to a certain location in a file object over SFTP.

        :param file_obj: `ssh2.sftp.SFTPHandle` to interact with.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        :param offset: What location to seek to in the file.
        :type offset: ``int``
        :return: ``None``
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            self.ssh_session._block(file_obj.seek64,offset)

    def write(self,file_obj,data_bytes):
        '''
        Write to a file object over SFTP on the remote server.

        :param file_obj: `ssh2.sftp.SFTPHandle` to interact with.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        :param data_bytes: Bytes to write to the file with.
        :type data_bytes: ``byte str``
        :return: ``None``
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            self.ssh_session._block_write(file_obj.write,data_bytes)

    def read(self,file_obj,iter=True):
        '''
        Read from file object over SFTP on the remote server.

        :param file_obj: `ssh2.sftp.SFTPHandle` to interact with.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        :param iter: Flag for if you want the iterable object instead of just a byte string returned.
        :type iter: ``bool``
        :return: ``byte str`` or ``iter``
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            if iter==True:
                return(self.ssh_session._read_iter(file_obj.read,True))
            elif iter==False:
                data = b''
                for chunk in self.ssh_session._read_iter(file_obj.read,True):
                    data+=chunk
                return(data)

    def close(self,file_obj):
        '''
        Closes a file object over SFTP on the remote server. It is a good idea to delete the ``file_obj`` after calling this.

        :param file_obj: `ssh2.sftp.SFTPHandle` to interact with.
        :type file_obj: `ssh2.sftp.SFTPHandle`
        :return: ``None``
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            self.fsync(file_obj)
            self.ssh_session._block(file_obj.close)

    def put_folder(self,local_path,remote_path):
        '''
        Upload an entire folder via SFTP to the remote session. Similar to ``cp -r /files/* /target``
        Also retains file permissions.
        Local path must be a directory to upload, if a path to a file is provided, nothing will happen.

        :param local_path: The local path, on the machine where your code is running from, to upload from.
        :type local_path: ``str``
        :param remote_path: The remote path to upload the ``local_path`` to.
        :type remote_path: ``str``
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            if os.path.isdir(local_path)==True:
                try:
                    self.mkdir(remote_path,os.stat(local_path).st_mode)
                except libssh2.exceptions.SFTPProtocolError:
                    pass
                for (dirpath,dirnames,filenames) in os.walk(local_path):
                    for dirname in sorted(dirnames):
                        local_dir_path = os.path.join(dirpath,dirname)
                        tmp_rpath = local_dir_path[len(local_path):]
                        if tmp_rpath.startswith(os.path.sep):
                            tmp_rpath = tmp_rpath[1:]
                        remote_dir_path = os.path.join(remote_path,tmp_rpath)
                        if not dirname in self.list_dir(remote_path):
                            self.mkdir(remote_dir_path,os.stat(local_dir_path).st_mode)
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

        :param local_path: The local path, on the machine where your code is running from, to upload from.
        :type local_path: ``str``
        :param remote_path: The remote path to upload the ``local_path`` to.
        :type remote_path: ``str``
        '''
        if self.ssh_session.__check_for_attr__('sftp'):
            f = self.open(remote_path,libssh2.LIBSSH2_FXF_WRITE|libssh2.LIBSSH2_FXF_CREAT|libssh2.LIBSSH2_FXF_TRUNC,os.stat(local_path).st_mode)
            self.write(f,open(local_path,'rb').read())
            self.close(f)

class RedSFTPFile(object):
    '''
    Interact with files over SFTP using a class rather than passing a file handle around.

    .. warning::
    This class simply uses the functions from `redssh.sftp.RedSFTP` minus any requirement for the `file_obj` argument for calls.

    :param sftp: `redssh.sftp.RedSFTP` object from the session you'd like to interact via.
    :type sftp: `redssh.sftp.RedSFTP`
    :param remote_path: Path that file is located at on the remote server.
    :type remote_path: ``str``
    :param sftp_flags: Flags for the SFTP session to understand what you are going to do with the file.
    :type sftp_flags: ``int``
    :param file_mode: File mode for the file being opened.
    :type file_mode: ``int``
    '''
    def __init__(self,sftp,remote_path,sftp_flags,file_mode):
        self.sftp = sftp
        self.remote_path = remote_path
        self.sftp_flags = sftp_flags
        self.file_mode = file_mode
        self.open()

    def __check_for_attr__(self,attr):
        return(attr in self.__dict__)

    def __del__(self):
        self.close()

    def open(self):
        if self.__check_for_attr__('file_obj')==False:
            self.file_obj = self.sftp.ssh_session._block(self.sftp.client.open,self.remote_path,self.sftp_flags,self.file_mode)

    def fsetstat(self,*args,**kwargs):
        return(self.sftp.fsetstat(self.file_obj,*args,**kwargs))

    def fstat(self):
        return(self.sftp.fstat(self.file_obj))

    def fstatvfs(self):
        return(self.sftp.fstatvfs(self.file_obj))

    def fsync(self):
        return(self.sftp.fsync(self.file_obj))

    def read(self,*args,**kwargs):
        return(self.sftp.read(self.file_obj,*args,**kwargs))

    def rewind(self):
        return(self.sftp.rewind(self.file_obj))

    def seek(self,*args,**kwargs):
        return(self.sftp.seek(self.file_obj,*args,**kwargs))

    def write(self,*args,**kwargs):
        return(self.sftp.write(self.file_obj,*args,**kwargs))

    def close(self):
        if self.__check_for_attr__('file_obj')==True:
            self.sftp.close(self.file_obj)
            del self.file_obj




