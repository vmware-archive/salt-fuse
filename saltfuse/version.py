# -*- coding: utf-8 -*-
'''
Set up the version of Salt
'''

# Import python libs
import sys
import pkg_resources

# Import salt libs
from salt.version import SaltStackVersion, __version__ as __saltversion__


# ----- Hardcoded Salt Fuse Version Information ------------------------------>
#
# Please bump version information for __saltstack_version__ on new releases
# ----------------------------------------------------------------------------
__saltstack_version__ = SaltStackVersion(0, 4, 0)
__version_info__ = __saltstack_version__.info
__version__ = __saltstack_version__.string
# <---- Hardcoded Salt Fuse Version Information -------------------------------


# ----- Dynamic/Runtime Salt Fuse Version Information ------------------------>
def __get_version(version, version_info):
    '''
    If we can get a version provided at installation time or from Git, use
    that instead, otherwise we carry on.
    '''
    try:
        # Try to import the version information provided at install time
        from saltfuse._version import __version__, __version_info__  # pylint: disable=E0611
        return __version__, __version_info__
    except ImportError:
        pass

    # This might be a 'python setup.py develop' installation type. Let's
    # discover the version information at runtime.
    import os
    import warnings
    import subprocess

    if 'SETUP_DIRNAME' in globals():
        # This is from the exec() call in Salt Fuse's setup.py
        cwd = SETUP_DIRNAME  # pylint: disable=E0602
        if not os.path.exists(os.path.join(cwd, '.git')):
            # This is not a Salt Fuse git checkout!!! Don't even try to parse...
            return version, version_info
    else:
        cwd = os.path.abspath(os.path.dirname(__file__))
        if not os.path.exists(os.path.join(os.path.dirname(cwd), '.git')):
            # This is not a Salt git checkout!!! Don't even try to parse...
            return version, version_info

    try:
        kwargs = dict(
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd
        )

        if not sys.platform.startswith('win'):
            # Let's not import `salt.utils` for the above check
            kwargs['close_fds'] = True

        process = subprocess.Popen(
                ['git', 'describe', '--tags', '--match', 'v[0-9]*'], **kwargs)
        out, err = process.communicate()
        out = out.strip()
        err = err.strip()

        if not out or err:
            return version, version_info

        parsed_version = SaltStackVersion.parse(out)

        if parsed_version.info > version_info:
            warnings.warn(
                'The parsed version info, `{0}`, is bigger than the one '
                'defined in the file, `{1}`. Missing version bump?'.format(
                    parsed_version.info,
                    version_info
                ),
                UserWarning,
                stacklevel=2
            )
            return version, version_info
        elif parsed_version.info < version_info:
            warnings.warn(
                'The parsed version info, `{0}`, is lower than the one '
                'defined in the file, `{1}`.'
                'In order to get the proper salt version with the git hash '
                'you need to update salt\'s local git tags. Something like: '
                '\'git fetch --tags\' or \'git fetch --tags upstream\' if '
                'you followed salt\'s contribute documentation. The version '
                'string WILL NOT include the git hash.'.format(
                    parsed_version.info,
                    version_info
                ),
                UserWarning,
                stacklevel=2
            )
            return version, version_info
        return parsed_version.string, parsed_version.info
    except OSError as os_err:
        if os_err.errno != 2:
            # If the errno is not 2(The system cannot find the file
            # specified), raise the exception so it can be catch by the
            # developers
            raise
    return version, version_info


# Get additional version information if available
__version__, __version_info__ = __get_version(__version__, __version_info__)
# This function has executed once, we're done with it. Delete it!
del __get_version
# <---- Dynamic/Runtime Salt Version Information -----------------------------


def versions_information():
    '''
    Report on all of the versions for dependent software
    '''

    libs = [
        ('Salt Fuse', None, __version__),
        ('Python', None, sys.version.rsplit('\n')[0].strip()),
        ('Salt', None, __saltversion__),
        ('FusePy', None, pkg_resources.get_distribution('fusepy').version)
    ]

    for name, imp, attr in libs:
        if imp is None:
            yield name, attr
            continue
        try:
            imp = __import__(imp)
            version = getattr(imp, attr)
            if callable(version):
                version = version()
            if isinstance(version, (tuple, list)):
                version = '.'.join(map(str, version))
            yield name, version
        except ImportError:
            yield name, None


def versions_report():
    '''
    Yield each library properly formatted for a console clean output.
    '''
    libs = list(versions_information())

    padding = max(len(lib[0]) for lib in libs) + 1

    fmt = '{0:>{pad}}: {1}'

    for name, version in libs:
        yield fmt.format(name, version or 'Not Installed', pad=padding)


if __name__ == '__main__':
    print(__version__)
