
from redssh import utils

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
        self.__check_for_attr__ = utils.check_for_attr
        self.sftp = sftp
        self.remote_path = remote_path
        self.sftp_flags = sftp_flags
        self.file_mode = file_mode
        self.open()

    def __del__(self):
        self.close()

    def open(self):
        if self.__check_for_attr__(self,'file_obj')==False:
            self.file_obj = self.sftp.ssh_session._block(self.sftp.client.open,self.remote_path,self.sftp_flags,self.file_mode)

    def fsetstat(self,*args,**kwargs):
        return(self.sftp.setstat(self.remote_path,*args,**kwargs))

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
        if self.__check_for_attr__(self,'file_obj')==True:
            self.sftp.close(self.file_obj)
            del self.file_obj
