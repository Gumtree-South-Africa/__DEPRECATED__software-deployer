from deployerlib.exceptions import DeployerException

from fabric.api import env
from fabric.state import output
from fabric.contrib import files
from fabric.context_managers import settings
from fabric.operations import run, sudo, put


class FabricHelper(object):
    """Handle remote execution"""

    def __init__(self, username='', host='', pool_size=1, caller=None):

        env.user = username
        env.host_string = host

        env.warn_only = True
        env.abort_on_prompts = True
        output.everything = False
        env.parallel = False
        env.serial = True

    def __repr__(self):

        return '{0}(user={1}, parallel={2}, pool_size={3})'.format(self.__class__.__name__,
          env.user, env.parallel, env.pool_size)

    def put_remote(self, local_file, remote_dir, **fabric_settings):
        """Upload a file to a remote host"""

        with settings(**fabric_settings):
            return put(local_file, remote_dir)

    def file_exists(self, remote_file, **fabric_settings):
        """Check whether a file exists on a remote server"""

        with settings(**fabric_settings):
            return files.exists(remote_file)

    def execute_remote(self, command, use_sudo=False, **fabric_settings):
        """Execute a command via fabric"""

        with settings(**fabric_settings):
            if use_sudo:
                return sudo(command)
            else:
                return run(command)
