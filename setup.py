# -*- coding: utf-8 -*-
#!/usr/bin/env python
'''
The setup script for salt-fuse
'''

# pylint: disable=C0111,E1101,E1103,F0401,W0611

# For Python 2.5.  A no-op on 2.6 and above.
from __future__ import with_statement

import os
import sys
import glob
import urllib2
from datetime import datetime
# pylint: disable=E0611
from distutils import log
from distutils.cmd import Command
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.command.sdist import sdist
# pylint: enable=E0611

# Change to salt source's directory prior to running any command
try:
    SETUP_DIRNAME = os.path.dirname(__file__)
except NameError:
    # We're most likely being frozen and __file__ triggered this NameError
    # Let's work around that
    SETUP_DIRNAME = os.path.dirname(sys.argv[0])

if SETUP_DIRNAME != '':
    os.chdir(SETUP_DIRNAME)

SETUP_DIRNAME = os.path.abspath(SETUP_DIRNAME)

# Use setuptools only if the user opts-in by setting the USE_SETUPTOOLS env var
# Or if setuptools was previously imported (which is the case when using
# 'distribute')
# This ensures consistent behavior but allows for advanced usage with
# virtualenv, buildout, and others.
WITH_SETUPTOOLS = False
if 'USE_SETUPTOOLS' in os.environ or 'setuptools' in sys.modules:
    try:
        from setuptools import setup
        from setuptools.command.install import install
        from setuptools.command.sdist import sdist
        WITH_SETUPTOOLS = True
    except ImportError:
        WITH_SETUPTOOLS = False

if WITH_SETUPTOOLS is False:
    import warnings
    # pylint: disable=E0611
    from distutils.command.install import install
    from distutils.core import setup
    # pylint: enable=E0611
    warnings.filterwarnings(
        'ignore',
        'Unknown distribution option: \'(tests_require|install_requires|zip_safe)\'',
        UserWarning,
        'distutils.dist'
    )

try:
    # Add the esky bdist target if the module is available
    # may require additional modules depending on platform
    from esky import bdist_esky
    # bbfreeze chosen for its tight integration with distutils
    import bbfreeze
    HAS_ESKY = True
except ImportError:
    HAS_ESKY = False

SALT_FUSE_VERSION = os.path.join(
    os.path.abspath(SETUP_DIRNAME), 'saltfuse', 'version.py'
)

SALT_FUSE_REQS = os.path.join(
    os.path.abspath(SETUP_DIRNAME), 'requirements.txt'
)

# pylint: disable=W0122
exec(compile(open(SALT_FUSE_VERSION).read(), SALT_FUSE_VERSION, 'exec'))
# pylint: enable=W0122


class Clean(clean):
    def run(self):
        clean.run(self)
        # Let's clean compiled *.py[c,o]
        remove_extensions = ('.pyc', '.pyo')
        for subdir in ('salt', 'tests', 'doc'):
            root = os.path.join(os.path.dirname(__file__), subdir)
            for dirname, dirnames, filenames in os.walk(root):
                for to_remove_filename in glob.glob(
                        '{0}/*.py[oc]'.format(dirname)):
                    os.remove(to_remove_filename)


INSTALL_VERSION_TEMPLATE = '''\
# This file was auto-generated by salt-fuse's setup on \
{date:%A, %d %B %Y @ %H:%m:%S UTC}.

__version__ = {version!r}
__version_info__ = {version_info!r}
'''


class Build(build):
    def run(self):
        # Run build.run function
        build.run(self)
        if getattr(self.distribution, 'running_salt_install', False):
            # If our install attribute is present and set to True, we'll go
            # ahead and write our install time python modules.

            # Write the version file
            version_file_path = os.path.join(
                self.build_lib, 'saltfuse', '_version.py'
            )
            # pylint: disable=E0602
            open(version_file_path, 'w').write(
                INSTALL_VERSION_TEMPLATE.format(
                    date=datetime.utcnow(),
                    version=__version__,
                    version_info=__version_info__
                )
            )
            # pylint: enable=E0602


class Install(install):

    def run(self):
        # Let's set the running_salt_install attribute so we can add
        # _version.py in the build command
        self.distribution.running_salt_install = True
        # Run install.run
        install.run(self)


NAME = 'SaltFuse'
VER = __version__  # pylint: disable=E0602
DESC = ('Portable, distributed, remote execution and '
        'configuration management system')

REQUIREMENTS = []
with open(SALT_FUSE_REQS) as rfh:
    for line in rfh.readlines():
        if not line or line.startswith('#'):
            continue
        REQUIREMENTS.append(line.strip())

SETUP_KWARGS = {'name': NAME,
                'version': VER,
                'description': DESC,
                'author': 'Joseph Hall',
                'author_email': 'jphall@saltstack.com',
                'url': 'http://saltstack.org',
                'cmdclass': {
                    'clean': Clean,
                    'build': Build,
                    'install': Install
                },
                'classifiers': ['Programming Language :: Python',
                                'Programming Language :: Cython',
                                'Programming Language :: Python :: 2.6',
                                'Programming Language :: Python :: 2.7',
                                'Development Status :: 3 - Alpha'
                                'Environment :: Console',
                                'Intended Audience :: Developers',
                                'Intended Audience :: Information Technology',
                                'Intended Audience :: System Administrators',
                                ('License :: OSI Approved ::'
                                 ' Apache Software License'),
                                'Operating System :: POSIX :: Linux',
                                'Topic :: System :: Clustering',
                                'Topic :: System :: Distributed Computing',
                                ],
                'packages': ['saltfuse'],
                # Required for esky builds
                'install_requires': REQUIREMENTS,
                # The dynamic module loading in salt.modules makes this
                # package zip unsafe. Required for esky builds
                'zip_safe': False
                }


if WITH_SETUPTOOLS:
    SETUP_KWARGS['entry_points'] = {
        'console_scripts': ['salt-fuse = saltfuse.cli:main']
    }
else:
    SETUP_KWARGS['scripts'] = ['scripts/salt-fuse']


if __name__ == '__main__':
    setup(**SETUP_KWARGS)