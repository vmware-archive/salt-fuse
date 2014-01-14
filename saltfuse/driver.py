# -*- coding: utf-8 -*-
'''
This code is currently considered to be in an alpha state; use at your own risk!

Requires the fusepy library to be installed:

https://github.com/terencehonles/fusepy
'''

# Import python libs
from __future__ import with_statement
import os
import os.path
import pprint
import tempfile

# Import salt libs
import salt.client

# Import 3rd-party libs
from fuse import FuseOSError, Operations, LoggingMixIn

open_files = {}


class SaltFuseDriver(LoggingMixIn, Operations):
    def __init__(self, opts, root, minion_id):
        print('Initializing salt-fuse')
        print('Root: {0}'.format(root))
        print('ID: {0}'.format(minion_id))
        self.opts = opts
        self.root = os.path.realpath(root)
        self.minion_id = minion_id
        self.client = salt.client.LocalClient(
            self.opts.get('master_config',
                          os.path.join(os.path.dirname(self.opts['conf_file']),
                                       'master')
            )
        )

    def _full_path(self, partial):
        print('_full_path is {0}'.format(partial))
        if partial.startswith('/'):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    def _salt_cmd(self, fun, arg=None, kwarg=None):
        if not arg:
            arg = ()
        if not kwarg:
            kwarg = {}

        ret = self.client.cmd(
            self.minion_id,
            fun,
            arg=arg,
            kwarg=kwarg,
            timeout=5,
        )
        return ret[self.minion_id]

    def access(self, path, mode):
        print('function access')
        full_path = self._full_path(path)
        return self._salt_cmd(
            'file.access',
            kwarg={
                'path': full_path,
                'mode': mode,
            },
        )

    def chmod(self, path, mode):
        print('function chmod')
        mode = oct(mode)
        mode = str(mode).replace('L', '')
        mode = mode[-4:]
        return self._salt_cmd(
            'cmd.run',
            arg=[
                'chmod {0} {1}'.format(mode, full_path),
            ],
        )

    def chown(self, path, uid, gid):
        print('function chown')
        return self._salt_cmd(
            'cmd.run',
            arg=[
                'chown {0}.{1} {2}'.format(uid, gid, full_path),
            ],
        )

    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        print('function getattr: {0}, {1}, {2}'.format(path, full_path, fh))
        ret = self._salt_cmd(
            'file.lstat',
            kwarg={
                'path': full_path,
            },
        )
        if not ret:
            raise OSError(2, 'No such file or directory: {0}'.format(full_path))

        return ret

    def link(self, target, source):
        print('function link')
        res = self._salt_cmd(
            'file.link',
            kwarg={
                'src': self._full_path(source),
                'link': target,
            },
        )
        return

    def mkdir(self, path, mode):
        print('function mkdir')
        full_path = self._full_path(path)
        res = self._salt_cmd(
            'file.mkdir',
            kwarg={
                'dir_path': full_path,
                'mode': mode,
            },
        )
        return

    def mknod(self, path, mode, device):
        print('function mknod')
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
                'name': full_path,
                'ntype': ntype,
                'major': major,
                'minor': minor,
            },
        )
        return

    def readdir(self, path, fh):
        full_path = self._full_path(path)
        print('function readdir: {0}, {1}'.format(path, full_path))

        return self._salt_cmd(
            'file.readdir',
            kwarg={
                'path': full_path,
            },
        )

    def readlink(self, path):
        full_path = self._full_path(path)
        print('function readlink: {0}, {1}'.format(path, full_path))
        return self._salt_cmd(
            'file.readlink',
            kwarg={
                'path': full_path,
            },
        )

    def rename(self, src, dst):
        print('function rename')
        self._salt_cmd(
            'file.rename',
            kwarg={
                'src': src,
                'dst': self._full_path(dst),
            },
        )
        return

    def rmdir(self, path):
        print('function rmdir')
        pprint.pprint(path)
        self._salt_cmd(
            'file.rmdir',
            kwarg={
                'path': full_path,
            },
        )
        return

    def statfs(self, path, fh=None):
        print('function statfs')
        full_path = self._full_path(path)
        ret = self._salt_cmd(
            'file.statvfs',
            kwarg={
                'path': full_path,
            },
        )
        pprint.pprint(ret)
        return ret

    def symlink(self, target, source):
        print('function symlink')
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
        print('function unlink')
        full_path = self._full_path(path)

        isdir = self._salt_cmd(
            'file.directory_exists',
            kwarg={
                'path': full_path,
            },
        )
        if isdir:
            raise OSError

        self._salt_cmd(
            'file.remove',
            kwarg={
                'path': full_path,
            },
        )
        return

    def utimens(self, path, times=None):
        print('function utimens')
        full_path = self._full_path(path)

        kwarg = {
            'name': full_path,
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
        full_path = self._full_path(path)
        print('function open')
        tmpfh, tmppath = tempfile.mkstemp()
        open_files[str(full_path)] = {'tmpfh': tmpfh, 'tmppath': str(tmppath)}
        return tmpfh

    def create(self, path, mode):
        full_path = self._full_path(path)
        print('function create ({0}), mode {1}'.format(path, mode))
        ret = self.open(full_path)
        pprint.pprint(ret)
        return ret

    def read(self, path, size, offset, fh):
        print('function read')
        full_path = self._full_path(path)
        ret = self._salt_cmd(
            'file.seek_read',
            kwarg={
                'path': full_path,
                'size': size,
                'offset': str(offset),
            },
        )
        return ret

    def write(self, path, data, offset, fh):
        full_path = self._full_path(path)
        print('function write, path is {0}, offset is {1}'.format(path, offset))
        ret = self._salt_cmd(
            'file.seek_write',
            kwarg={
                'path': full_path,
                'data': data,
                'offset': str(offset),
            },
        )
        return ret

    def flush(self, path, fh):
        print('function flush')
        return

    def fsync(self, path, datasync, fh):
        print('function fsync')
        return

    def truncate(self, path, length, fh=None):
        print('function truncate')
        full_path = self._full_path(path)
        ret = self._salt_cmd(
            'file.truncate',
            kwarg={
                'path': full_path,
                'length': str(length),
            },
        )
        return

    def release(self, path, fh):
        full_path = self._full_path(path)
        print('function release')
        pprint.pprint(open_files)
        if str(full_path) in open_files:
            os.remove(open_files[str(full_path)]['tmppath'])
            del open_files[str(full_path)]
        return
