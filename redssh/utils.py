# RedSSH
# Copyright (C) 2022 - 2022 Red_M ( http://bitbucket.com/Red_M )

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


def repl_setattr(self, attr, value):
    setattr(getattr(self.obj, self.sub_obj), attr, value)

class ObjectProxy(object):
    def __init__(self, obj, sub_obj):
        self.obj = obj
        self.sub_obj = sub_obj
        self.____init____done____ = True

    def __getattr__(self, attr):
        return(getattr(getattr(self.obj, self.sub_obj), attr))

    def __setattr__(self, attr, value):
        if '____init____done____' in self.__dict__ and attr!='____init____done____' and attr!=repl_setattr:
            repl_setattr(self, attr, value)
            super().__setattr__('__setattr__', repl_setattr)
        else:
            super().__setattr__(attr, value)


def check_for_attr(self,attr):
    return(attr in self.__dict__)
