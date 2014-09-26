import time

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException

from fabric.api import env
from fabric.state import output
from fabric.tasks import execute
from fabric.contrib import files
from fabric.context_managers import settings
from fabric.operations import run, sudo, put


class FabricHelper(object):
    """Handle remote execution"""

    def __init__(self, username=None, pool_size=0):
        self.log = Log(self.__class__.__name__)

        env.warn_only = True
        output.everything = False

        if username:
            env.user = username

        self.set_pool_size(pool_size)

    def __repr__(self):

        return '{0}(user={1}, parallel={2}, pool_size={3})'.format(self.__class__.__name__,
          env.user, env.parallel, env.pool_size)

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
            self.log.info('Setting default fabric pool_size to {0}'.format(pool_size))
            env.pool_size = pool_size
            env.parallel = True
            env.serial = False
        else:
            self.disable_parallel()

    def get_pool_size(self):
        return env.pool_size

    def disable_parallel(self):
        """Disable parallel"""

        self.log.info('Disabling parallel execution')
        env.pool_size = 1
        env.parallel = False
        env.serial = True

    def put_remote(self, local_file, remote_dir, **fabric_settings):
        """Upload a file to a remote host"""

        with settings(**fabric_settings):
            return execute(put, local_file, remote_dir)

    def file_exists(self, remote_file, **fabric_settings):
        """Check whether a file exists on a remote server"""

        with settings(**fabric_settings):
            return execute(files.exists, remote_file)

    def execute_remote(self, command, use_sudo=False, **fabric_settings):
        """Execute a command via fabric"""

        with settings(**fabric_settings):
            if use_sudo:
                return execute(sudo, command)
            else:
                return execute(run, command)

    def _restart_service(self, stop_command, start_command, check_command, timeout, use_sudo):

        if use_sudo:
            call = sudo
        else:
            call = run

        res = call(stop_command)

        if res.failed:
            raise DeployerException('Failed to stop service: {0}'.format(res))

        if check_command:
            timeout = time.time() + timeout
            success = False

            while time.time() < timeout:
                time.sleep(2)
                res = run(check_command)

                if res.return_code != 0:
                    success = True
                    break

            if success:
                self.log.info('Stopped: {0}'.format(res))
            else:
                raise DeployerException('Failed to stop service: {0}'.format(res))

        if start_command:
            res = call(start_command)

            if res.failed:
                raise DeployerException('Failed to start service: {0}'.format(res))

        if check_command:
            timeout = time.time() + timeout
            success = False

            while time.time() < timeout:
                time.sleep(2)
                res = run(check_command)

                if res.return_code == 0:
                    success = True
                    break

            if success:
                self.log.info('Started: {0}'.format(res))
            else:
                raise DeployerException('Failed to start service: {0}'.format(res))

    def restart_service(self, stop_command, start_command=None, check_command=None, timeout=60, use_sudo=True, **fabric_settings):
        """External method for restarting a remote service"""

        with settings(**fabric_settings):
            return execute(self._restart_service, stop_command, start_command, check_command, timeout, use_sudo)
