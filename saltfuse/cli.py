# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2014 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    saltfuse.cli
    ~~~~~~~~~~~~

    CLI access to Salt Fuse
'''

# Import salt libs
from salt.utils.verify import verify_files

# Import salt fuse libs
from saltfuse.driver import SaltFuseDriver
from saltfuse.parser import SaltFuseParser

# Import 3rd-party libs
from fuse import FUSE


class SaltFuse(SaltFuseParser):
    '''
    The execution of salt-fuse happens here
    '''

    def run(self):
        self.parse_args()

        if self.config['verify_env']:
            if not self.config['log_file'].startswith(('tcp://',
                                                       'udp://',
                                                       'file://')):
                # Logfile is not using Syslog, verify
                verify_files(
                    [self.config['log_file']],
                    self.config['user']
                )

        # Setup file logging!
        self.setup_logfile_logger()

        driver = FUSE(
            SaltFuseDriver(self.config),
            self.mount_path,
            foreground=True
        )


def main():
    parser = SaltFuse()
    parser.run()
