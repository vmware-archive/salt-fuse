# -*- coding: utf-8 -*-
'''
This code is currently considered to be in an alpha state; use at your own risk!

Requires the fusepy library to be installed:

https://github.com/terencehonles/fusepy
'''

# Import python libs
import time
import os
import os.path
import pprint
import tempfile
import logging

# Import salt libs
import salt.client

# Import 3rd-party libs
from fuse import FuseOSError, Operations, LoggingMixIn

log = logging.getLogger(__name__)

open_files = {}


class SaltFuseDriver(LoggingMixIn, Operations):
    def __init__(self, opts):
        root = '/'
        log.debug('Initializing salt-fuse')
        log.debug('Root: {0}'.format(root))
        log.debug(self._list_minions())
        self.opts = opts
        self.root = os.path.realpath(root)
        self.stamp = time.time()
        self.client = salt.client.LocalClient(
            self.opts.get('master_config',
                          os.path.join(os.path.dirname(self.opts['conf_file']),
                                       'master')
            )
        )

    def _list_minions(self):
        return os.listdir('/etc/salt/pki/master/minions/')

    def _full_path(self, partial):
        log.debug('_full_path is {0}'.format(partial))
        if partial.startswith('/'):
            partial = partial[1:]
        comps = partial.split('/')
        if not comps:
            return None, None
        minion_id = comps[0]
        partial = '/'.join(comps[1:])
        path = os.path.join(self.root, partial)
        return path, minion_id

    def _salt_cmd(self, minion_id, fun, arg=None, kwarg=None):
        if not arg:
            arg = ()
        if not kwarg:
            kwarg = {}

        ret = self.client.cmd(
            minion_id,
            fun,
            arg=arg,
            kwarg=kwarg,
            timeout=5,
        )
        #return ret[self.minion_id]
        return ret[minion_id]

    def access(self, path, mode):
        log.debug('function access')
        full_path, minion_id = self._full_path(path)
        return self._salt_cmd(
            minion_id,
            'file.access',
            kwarg={
                'path': full_path,
                'mode': mode,
            },
        )

    def chmod(self, path, mode):
        log.debug('function chmod')
        mode = oct(mode)
        mode = str(mode).replace('L', '')
        mode = mode[-4:]
        return self._salt_cmd(
            minion_id,
            'cmd.run',
            arg=[
                'chmod {0} {1}'.format(mode, full_path),
            ],
        )

    def chown(self, path, uid, gid):
        log.debug('function chown')
        return self._salt_cmd(
            minion_id,
            'cmd.run',
            arg=[
                'chown {0}.{1} {2}'.format(uid, gid, full_path),
            ],
        )

    def getattr(self, path, fh=None):
        full_path, minion_id = self._full_path(path)
        log.debug('function getattr: {0}, {1}, {2}'.format(path, full_path, fh))

        if full_path == '/':
            return {
                'st_atime': self.stamp,
                'st_ctime': self.stamp,
                'st_gid': 0,
                'st_mode': 16877,
                'st_mtime': self.stamp,
                'st_nlink': 7,
                'st_size': 4096,
                'st_uid': 0,
            }

        ret = self._salt_cmd(
            minion_id,
            'file.lstat',
            kwarg={
                'path': full_path,
            },
        )
        if not ret:
            raise OSError(2, 'No such file or directory: {0}'.format(full_path))

        return ret

    def link(self, target, source):
        log.debug('function link')
        res = self._salt_cmd(
            minion_id,
            'file.link',
            kwarg={
                'src': self._full_path(source),
                'link': target,
            },
        )
        return

    def mkdir(self, path, mode):
        log.debug('function mkdir')
        full_path, minion_id = self._full_path(path)
        res = self._salt_cmd(
            minion_id,
            'file.mkdir',
            kwarg={
                'dir_path': full_path,
                'mode': mode,
            },
        )
        return

    def mknod(self, path, mode, device):
        log.debug('function mknod')
        full_path, minion_id = self._full_path(path)

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
            minion_id,
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
        full_path, minion_id = self._full_path(path)
        log.debug('function readdir: {0}, {1}'.format(path, full_path))

        if not minion_id:
            return self._list_minions()

        return self._salt_cmd(
            minion_id,
            'file.readdir',
            kwarg={
                'path': full_path,
            },
        )

    def readlink(self, path):
        full_path, minion_id = self._full_path(path)
        log.debug('function readlink: {0}, {1}'.format(path, full_path))
        return self._salt_cmd(
            minion_id,
            'file.readlink',
            kwarg={
                'path': full_path,
            },
        )

    def rename(self, src, dst):
        log.debug('function rename')
        self._salt_cmd(
            minion_id,
            'file.rename',
            kwarg={
                'src': src,
                'dst': self._full_path(dst),
            },
        )
        return

    def rmdir(self, path):
        log.debug('function rmdir')
        self._salt_cmd(
            minion_id,
            'file.rmdir',
            kwarg={
                'path': full_path,
            },
        )
        return

    def statfs(self, path, fh=None):
        log.debug('function statfs')
        full_path, minion_id = self._full_path(path)
        ret = self._salt_cmd(
            minion_id,
            'file.statvfs',
            kwarg={
                'path': full_path,
            },
        )
        pprint.pprint(ret)
        return ret

    def symlink(self, target, source):
        log.debug('function symlink')
        if source.startswith('/'):
            # This gets tricky, trying to create symlinks outside the FUSE
            # filesystem. Here be dragons.
            pass
        else:
            source = '{0}/{1}'.format(self.root, source)
        self._salt_cmd(
            minion_id,
            'file.symlink',
            kwarg={
                'src': str(source),
                'link': str(target),
            },
        )
        return

    def unlink(self, path):
        log.debug('function unlink')
        full_path, minion_id = self._full_path(path)

        isdir = self._salt_cmd(
            minion_id,
            'file.directory_exists',
            kwarg={
                'path': full_path,
            },
        )
        if isdir:
            raise OSError

        self._salt_cmd(
            minion_id,
            'file.remove',
            kwarg={
                'path': full_path,
            },
        )
        return

    def utimens(self, path, times=None):
        log.debug('function utimens')
        full_path, minion_id = self._full_path(path)

        kwarg = {
            'name': full_path,
        }
        if times and times[0]:
            kwarg['atime'] = str(int(times[0]))
        if times and times[1]:
            kwarg['mtime'] = str(int(times[1]))

        ret = self._salt_cmd(
            minion_id,
            'file.touch',
            kwarg=kwarg,
        )
        return

    getxattr = None
    listxattr = None

    def open(self, path, flags=None):
        full_path, minion_id = self._full_path(path)
        log.debug('function open')
        tmpfh, tmppath = tempfile.mkstemp()
        open_files[str(full_path)] = {'tmpfh': tmpfh, 'tmppath': str(tmppath)}
        return tmpfh

    def create(self, path, mode):
        full_path, minion_id = self._full_path(path)
        log.debug('function create ({0}), mode {1}'.format(path, mode))
        ret = self.open(full_path)
        pprint.pprint(ret)
        return ret

    def read(self, path, size, offset, fh):
        log.debug('function read')
        full_path, minion_id = self._full_path(path)
        ret = self._salt_cmd(
            minion_id,
            'file.seek_read',
            kwarg={
                'path': full_path,
                'size': size,
                'offset': str(offset),
            },
        )
        return ret

    def write(self, path, data, offset, fh):
        full_path, minion_id = self._full_path(path)
        log.debug('function write, path is {0}, offset is {1}'.format(path, offset))
        ret = self._salt_cmd(
            minion_id,
            'file.seek_write',
            kwarg={
                'path': full_path,
                'data': data,
                'offset': str(offset),
            },
        )
        return ret

    def flush(self, path, fh):
        log.debug('function flush')
        return

    def fsync(self, path, datasync, fh):
        log.debug('function fsync')
        return

    def truncate(self, path, length, fh=None):
        log.debug('function truncate')
        full_path, minion_id = self._full_path(path)
        ret = self._salt_cmd(
            minion_id,
            'file.truncate',
            kwarg={
                'path': full_path,
                'length': str(length),
            },
        )
        return

    def release(self, path, fh):
        full_path, minion_id = self._full_path(path)
        log.debug('function release')
        pprint.pprint(open_files)
        if str(full_path) in open_files:
            os.remove(open_files[str(full_path)]['tmppath'])
            del open_files[str(full_path)]
        return
