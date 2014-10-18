from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class Unpack(object):
    """Unpack a packge on a remote host"""

    def __init__(self, remote_host, source, destination, config=None):
        self.log = Log(self.__class__.__name__)
        self.remote_host = remote_host
        self.source = source
        self.destination = destination
        self.command = self.get_unpack_command()

    def __repr__(self):
        return '{0}(remote_host={1}, source={2}, destination={3})'.format(self.__class__.__name__,
          repr(self.remote_host.hostname), repr(self.source), repr(self.destination))

    def get_unpack_command(self):
        """Based on the file extension, determine the command line to unpack the package"""

        if self.source.endswith('.tar.gz') or self.source.endswith('.tgz'):
            command = '/bin/tar xzf {0} -C {1}'.format(self.source, self.destination)
        elif self.source.endswith('.tar'):
            command = '/bin/tar xf {0} -C {1}'.format(self.source, self.destination)
        elif self.source.endswith('.war'):
            command = '/bin/cp {0} {1}'.format(self.source, self.destination)
        else:
            raise DeployerException('{0} class doesn\'t know how to unpack file: {1}'.format(
              self.__class__.__name__, self.source))

        self.log.debug('Usuing unpack command: {0}'.format(command))

        return command

    def execute(self, procname=None, remote_results={}):
        """Unpack the remote package"""

        if not self.remote_host.file_exists(self.destination):
            self.log.critical('Unpack destination does not exist: {0}'.format(self.destination))

        self.log.info('Unpacking {0}'.format(self.source))
        res = self.remote_host.execute_remote(self.command)

        if not res.succeeded:
            self.log.critical('Unpack failed: {0}'.format(res))

        remote_results[procname] = res.succeeded
        return res.succeeded
