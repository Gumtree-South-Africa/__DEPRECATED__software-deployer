import logging

from deployerlib.exceptions import DeployerException

from fabric.api import env
from fabric.tasks import execute
from fabric.contrib import files
from fabric.context_managers import settings
from fabric.operations import run, sudo, put


class FabricHelper(object):
    """Handle remote execution"""

    def __init__(self, username=None, pool_size=0):
        env.warn_only = True

        if username:
            env.user = username

        self.set_pool_size(pool_size)

    def set_pool_size(self, pool_size):
        """Set pool size for parallel execution
           - Disable parallel execution for pool_size less than 2
           - Disable parallel for non-numeric values of pool_size
        """

        try:
            pool_size = int(pool_size)
        except:
            self.disable_parallel()

        if pool_size > 1:
            logging.info('Setting fabric pool_size to {0}'.format(pool_size))
            env.pool_size = pool_size
            env.parallel = True
            env.serial = False
        else:
            self.disable_parallel()

    def get_pool_size(self):
        return env.pool_size

    def disable_parallel(self):
        """Disable parallel"""

        logging.info('Disabling parallel execution')
        env.pool_size = 1
        env.parallel = False
        env.serial = True

    def put_remote(self, local_file, remote_dir, **fabric_settings):
        """Upload a file to a remote host"""

        with settings(**fabric_settings):
            res = execute(put, local_file, remote_dir)

        return res

    def file_exists(self, remote_file, **fabric_settings):
        """Check whether a file exists on a remote server"""

        with settings(**fabric_settings):
            res = execute(files.exists, remote_file)

        return res

    def execute_remote(self, command, use_sudo=False, **fabric_settings):
        """Execute a command via fabric"""

        with settings(**fabric_settings):
            if use_sudo:
                return execute(sudo, command)
            else:
                return execute(run, command)

    def get_symlink_target(self, remote_file, **fabric_settings):
        """Get the target of a remote symlink"""

        return self.execute_remote('/bin/readlink {0}'.format(remote_file), **fabric_settings)
