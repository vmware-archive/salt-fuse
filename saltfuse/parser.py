# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2014 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    saltfuse.parser
    ~~~~~~~~~~~~~~~

    Salt Fuse CLI access options parser
'''

# Import python libs
import os
import sys

# Import salt libs
from salt import syspaths
from salt.utils.parsers import (ConfigDirMixIn, LogLevelMixIn, OptionParser,
                                OptionParserMeta)

# Import salt fuse libs
from saltfuse import config, version


class SaltFuseParser(OptionParser, ConfigDirMixIn, LogLevelMixIn):

    __metaclass__ = OptionParserMeta
    VERSION = version.__version__

    usage = '%prog [options] local_mount_path'

    # ConfigDirMixIn attributes
    _config_filename_ = 'fuse'

    # LogLevelMixIn attributes
    _default_logging_level_ = 'info'
    _logfile_config_setting_name_ = 'log_file'
    _loglevel_config_setting_name_ = 'log_level_logfile'
    _default_logging_logfile_ = os.path.join(syspaths.LOGS_DIR, 'fuse')

    def _mixin_after_parsed(self):
        if len(self.args) != 1:
            self.print_help()
            self.exit(1)

        [self.mount_path] = self.args

    def print_versions_report(self, file=sys.stdout):
        print >> file, '\n'.join(version.versions_report())
        self.exit()

    def setup_config(self):
        return config.fuse_config(self.get_config_file_path())
