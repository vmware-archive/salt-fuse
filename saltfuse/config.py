# -*- coding: utf-8 -*-
'''
    :codeauthor: :email:`Pedro Algarvio (pedro@algarvio.me)`
    :copyright: © 2014 by the SaltStack Team, see AUTHORS for more details.
    :license: Apache 2.0, see LICENSE for more details.


    saltfuse.config
    ~~~~~~~~~~~~~~~

    Salt Fuse Configuration
'''

# Import python libs
import os

# Import Salt libs
import salt.config
import salt.syspaths

# default configurations
DEFAULT_FUSE_OPTS = {
    'user': 'root',
    'cachedir': os.path.join(salt.syspaths.CACHE_DIR, 'fuse'),
    'conf_file': os.path.join(salt.syspaths.CONFIG_DIR, 'fuse'),
    'verify_env': True,
    'default_include': 'fuse.conf.d/*.conf',

    # Logging defaults
    'log_file': os.path.join(salt.syspaths.LOGS_DIR, 'fuse'),
    'log_level': None,
    'log_level_logfile': None,
    'log_datefmt': salt.config._DFLT_LOG_DATEFMT,
    'log_datefmt_logfile': salt.config._DFLT_LOG_DATEFMT_LOGFILE,
    'log_fmt_console': salt.config._DFLT_LOG_FMT_CONSOLE,
    'log_fmt_logfile': salt.config._DFLT_LOG_FMT_LOGFILE,
    'log_granular_levels': {},
}


def fuse_config(path, env_var='SALT_FUSE_CONFIG', defaults=None):
    if defaults is None:
        defaults = DEFAULT_FUSE_OPTS

    if not os.environ.get(env_var, None):
        # No valid setting was given using the configuration variable.
        # Lets see is SALT_CONFIG_DIR is of any use
        salt_config_dir = os.environ.get('SALT_CONFIG_DIR', None)
        if salt_config_dir:
            env_config_file_path = os.path.join(salt_config_dir, 'fuse')
            if salt_config_dir and os.path.isfile(env_config_file_path):
                # We can get a configuration file using SALT_CONFIG_DIR, let's
                # update the environment with this information
                os.environ[env_var] = env_config_file_path

    overrides = salt.config.load_config(
        path, env_var, DEFAULT_FUSE_OPTS['conf_file']
    )

    default_include = overrides.get('default_include',
                                    defaults['default_include'])
    include = overrides.get('include', [])

    overrides.update(
        salt.config.include_config(
            default_include, path, verbose=False
        )
    )
    overrides.update(
        salt.config.include_config(
            include, path, verbose=True
        )
    )

    opts = apply_fuse_config(overrides, defaults)
    return opts


def apply_fuse_config(overrides, defaults=None):
    if defaults is None:
        defaults = DEFAULT_FUSE_OPTS

    config = defaults.copy()

    if overrides:
        config.update(overrides)

    # set up the extension_modules location from the cachedir
    config['extension_modules'] = (
        config.get('extension_modules') or
        os.path.join(config['cachedir'], 'extmods')
    )

    return config
