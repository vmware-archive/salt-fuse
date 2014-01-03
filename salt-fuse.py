#!/usr/bin/env python
'''
This code is currently considered to be in an alpha state; use at your own risk!

Requires the fusepy library to be installed:

https://github.com/terencehonles/fusepy
'''

from __future__ import with_statement

from errno import EACCES
from os.path import realpath
from sys import argv, exit
from threading import Lock

import pprint
import os
import stat
import tempfile

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

import salt.client

tgt = argv[3]
open_files = {}

class SaltFuse(LoggingMixIn, Operations):
    def __init__(self, root):
        self.root = realpath(root)
        #self.rwlock = Lock()
        self.client = salt.client.LocalClient('/etc/salt')

    def __call__(self, op, path, *args):
        return super(SaltFuse, self).__call__(op, self.root + path, *args)

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def _salt_cmd(self, fun, arg=None, kwarg=None):
        if not arg:
            arg = ()
        if not kwarg:
            kwarg = {}

        ret = self.client.cmd(
            tgt,
            fun,
            arg=arg,
            kwarg=kwarg,
            timeout=5,
        )
        return ret[tgt]

    def access(self, path, mode):
        print('function: access')
        full_path = self._full_path(path)
        return self._salt_cmd(
            'file.access',
            kwarg={
                'path': full_path,
                'mode': mode,
            },
        )

    def chmod(self, path, mode):
        print('function: chmod')
        mode = oct(mode)
        mode = str(mode).replace('L', '')
        mode = mode[-4:]
        return self._salt_cmd(
            'cmd.run',
            arg=[
                'chmod {0} {1}'.format(mode, path),
            ],
        )


    def chown(self, path, uid, gid):
        print('function: chown')
        return self._salt_cmd(
            'cmd.run',
            arg=[
                'chown {0}.{1} {2}'.format(uid, gid, path),
            ],
        )

    def getattr(self, path, fh=None):
        print('function: getattr')
        full_path = self._full_path(path)
        ret = self._salt_cmd(
            'file.lstat',
            kwarg={
                'path': path,
            },
        )
        if not ret:
            raise OSError(2, 'No such file or directory: {0}'.format(full_path))

        return ret

    def link(self, target, source):
        print('function: link')
        res = self._salt_cmd(
            'file.link',
            kwarg={
                'src': self._full_path(source),
                'link': target,
            },
        )
        return

    def mkdir(self, path, mode):
        print('function: mkdir')
        full_path = self._full_path(path)
        res = self._salt_cmd(
            'file.mkdir',
            kwarg={
                'dir_path': path,
                'mode': mode,
            },
        )
        return

    def mknod(self, path, mode, device):
        print('function: mknod')
        full_path = self._full_path(path)

        devtype = str(oct(mode)).replace('L', '')
        if devtype[:2] == '01':
            ntype = 'p'
        elif devtype[:2] == '02':
            ntype = 'c'
        elif devtype[:2] == '06':
            ntype = 'b'
        else:
            raise OSError

        major = os.major(device)
        minor = os.minor(device)

        res = self._salt_cmd(
            'file.mknod',
            kwarg={
                'name': path,
                'ntype': ntype,
                'major': major,
                'minor': minor,
            },
        )
        return

    def readdir(self, path, fh):
        print('function: readdir')
        full_path = self._full_path(path)

        return self._salt_cmd(
            'file.readdir',
            kwarg={
                'path': path,
            },
        )

    def readlink(self, path):
        print('function: readlink')
        full_path = self._full_path(path)
        return self._salt_cmd(
            'file.readlink',
            kwarg={
                'path': path,
            },
        )

    def rename(self, src, dst):
        print('function: rename')
        self._salt_cmd(
            'file.rename',
            kwarg={
                'src': src,
                'dst': self._full_path(dst),
            },
        )
        return

    def rmdir(self, path):
        print('function: rmdir')
        pprint.pprint(path)
        self._salt_cmd(
            'file.rmdir',
            kwarg={
                'path': path,
            },
        )
        return

    def statfs(self, path, fh=None):
        print('function: statfs')
        full_path = self._full_path(path)
        ret = self._salt_cmd(
            'file.statvfs',
            kwarg={
                'path': path,
            },
        )
        pprint.pprint(ret)
        return ret

    def symlink(self, target, source):
        print('function: symlink')
        if source.startswith('/'):
            # This gets tricky, trying to create symlinks outside the FUSE
            # filesystem. Here be dragons.
            pass
        else:
            source = '{0}/{1}'.format(self.root, source)
        self._salt_cmd(
            'file.symlink',
            kwarg={
                'src': str(source),
                'link': str(target),
            },
        )
        return

    def unlink(self, path):
        print('function: unlink')
        full_path = self._full_path(path)

        isdir = self._salt_cmd(
            'file.directory_exists',
            kwarg={
                'path': path,
            },
        )
        if isdir:
            raise OSError

        self._salt_cmd(
            'file.remove',
            kwarg={
                'path': path,
            },
        )
        return

    def utimens(self, path, times=None):
        print('function: utimens')
        full_path = self._full_path(path)

        kwarg = {
            'name': path,
        }
        if times and times[0]:
            kwarg['atime'] = str(int(times[0]))
        if times and times[1]:
            kwarg['mtime'] = str(int(times[1]))

        ret = self._salt_cmd(
            'file.touch',
            kwarg=kwarg,
        )
        return

    getxattr = None
    listxattr = None

    def open(self, path, flags=None):
        print('function: open')
        tmpfh, tmppath = tempfile.mkstemp()
        open_files[str(path)] = {'tmpfh': tmpfh, 'tmppath': str(tmppath)}
        return tmpfh

    def create(self, path, mode):
        print('function: create ({0}), mode {1}'.format(path, mode))
        ret = self.open(path)
        pprint.pprint(ret)
        return ret

    def read(self, path, size, offset, fh):
        print('function: read')
        full_path = self._full_path(path)
        ret = self._salt_cmd(
            'file.seek_read',
            kwarg={
                'path': path,
                'size': size,
                'offset': str(offset),
            },
        )
        return ret

    def write(self, path, data, offset, fh):
        print('function: write, path is {0}, offset is {1}'.format(path, offset))
        full_path = self._full_path(path)
        ret = self._salt_cmd(
            'file.seek_write',
            kwarg={
                'path': path,
                'data': data,
                'offset': str(offset),
            },
        )
        return ret

    def flush(self, path, fh):
        print('function: flush')
        return

    def fsync(self, path, datasync, fh):
        print('function: fsync')
        return

    def truncate(self, path, length, fh=None):
        print('function: truncate')
        full_path = self._full_path(path)
        ret = self._salt_cmd(
            'file.truncate',
            kwarg={
                'path': path,
                'length': str(length),
            },
        )
        return

    def release(self, path, fh):
        print('function: release')
        pprint.pprint(open_files)
        if str(path) in open_files:
            os.remove(open_files[str(path)]['tmppath'])
            del open_files[str(path)]
        return


if __name__ == '__main__':
    fuse = FUSE(SaltFuse(argv[1]), argv[2], foreground=True)
