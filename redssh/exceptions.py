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

class RedSSHException(Exception):
    '''
    Base error class for sub classing.
    '''
    pass

class AuthenticationFailedException(RedSSHException):
    '''
    Failed to authenticate via supplied methods.
    '''
    def __init__(self, authentication):
        RedSSHException.__init__(self,'Failed to authenticated to remote server via: '+', '.join(authentication))


