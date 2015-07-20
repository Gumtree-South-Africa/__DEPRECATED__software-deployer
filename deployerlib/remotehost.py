from deployerlib.exceptions import DeployerException
from deployerlib.log import Log

from multiprocessing import Manager

from fabric.api import env
from fabric.state import output
from fabric.contrib import files
from fabric.context_managers import settings
from fabric.operations import run, sudo, put, get


class RemoteHost(object):
    """Handle execution of tasks on a remote host"""

    def __init__(self, hostname, username='', pool_size=1, caller=None):
        self.log = Log(self.__class__.__name__)

        self.hostname = hostname
        self.username = username

        env.user = username
        env.host_string = hostname

        env.warn_only = True
        env.abort_on_prompts = True
        output.everything = False
        env.parallel = False
        env.serial = True

    def __str__(self):
        return self.hostname

    def __repr__(self):

        return '{0}(hostname={1}, username={2})'.format(self.__class__.__name__,
          repr(self.hostname), repr(self.username))

    def put_remote(self, local_file, remote_dir, **fabric_settings):
        """Upload a file to a remote host"""

        self.log.debug('Putting local file "{0}" to remote dir "{1}"'.format(local_file, remote_dir))

        with settings(**fabric_settings):
            return put(local_file, remote_dir)

    def get_remote(self, remote_server_path, destination_path, **fabric_settings):
        """Retrieve file from a remote host"""

        self.log.debug('Getting remote file "{1}:{0}" to local "{2}"'.format(remote_server_path, self.hostname, destination_path))

        with settings(**fabric_settings):
            return get(remote_path=remote_server_path, local_path=destination_path)

    def file_exists(self, remote_file, **fabric_settings):
        """Check whether a file exists on a remote server"""

        self.log.debug('Checking existence of file {0}'.format(remote_file))

        with settings(**fabric_settings):
            return files.exists(remote_file)

    def execute_remote(self, command, use_sudo=False, output_hidebug=False, **fabric_settings):
        """Execute a command via fabric"""

        if use_sudo:
            self.log.debug('Executing command with sudo: {0}'.format(command))
        else:
            self.log.debug('Executing command: {0}'.format(command))

        with settings(**fabric_settings):
            if use_sudo:
                res = sudo(command, shell=False)
            else:
                res = run(command)

        if res:
            msg = 'Output: {0}'.format(res)
            if output_hidebug:
                self.log.hidebug(msg)
            else:
                self.log.debug(msg)

        return res
