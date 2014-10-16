from deployerlib.exceptions import DeployerException
from deployerlib.log import Log

from multiprocessing import Manager

from fabric.api import env
from fabric.state import output
from fabric.contrib import files
from fabric.context_managers import settings
from fabric.operations import run, sudo, put


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
          repr(env.host_string), repr(env.user))

    def put_remote(self, local_file, remote_dir, **fabric_settings):
        """Upload a file to a remote host"""

        self.log.debug('Putting local file "{0}" to remote dir "{1}"'.format(local_file, remote_dir))

        with settings(**fabric_settings):
            return put(local_file, remote_dir)

    def file_exists(self, remote_file, **fabric_settings):
        """Check whether a file exists on a remote server"""

        self.log.debug('Checking existence of file {0}'.format(remote_file))

        with settings(**fabric_settings):
            return files.exists(remote_file)

    def execute_remote(self, command, use_sudo=False, **fabric_settings):
        """Execute a command via fabric"""

        self.log.debug('Executing command "{0}" with use_sudo={1}'.format(command, use_sudo))

        with settings(**fabric_settings):
            if use_sudo:
                return sudo(command)
            else:
                return run(command)


def get_host_by_hostname(hostname, username=''):
    """Get or create a host object"""

    match = [x for x in all_hosts if x.hostname == hostname]

    if len(match) == 1:
        return match[0]
    elif len(match) > 1:
        raise DeployerException('More than one host found with hostname{0}'.format(hostname))
    else:
        host = RemoteHost(hostname, username)
        all_hosts.append(host)
        return host


all_hosts = []
