from deployerlib.command import Command


class Unpack(Command):
    """Unpack a packge on a remote host"""

    def verify(self, remote_host, source, destination):
        self.command = self.get_unpack_command()

        if not self.command:
            self.log.critical('{0} class doesn\'t know how to unpack file: {1}'.format(
              self.__class__.__name__, self.source))
            return False

        return True

    def get_unpack_command(self):
        """Based on the file extension, determine the command line to unpack the package"""

        if self.source.endswith('.tar.gz') or self.source.endswith('.tgz'):
            command = '/bin/tar xzf {0} -C {1}'.format(self.source, self.destination)
        elif self.source.endswith('.tar'):
            command = '/bin/tar xf {0} -C {1}'.format(self.source, self.destination)
        elif self.source.endswith('.war'):
            command = '/bin/cp {0} {1}'.format(self.source, self.destination)
        else:
            return False

        self.log.debug('Using unpack command: {0}'.format(command))

        return command

    def execute(self):
        """Unpack the remote package"""

        if not self.remote_host.file_exists(self.destination):
            self.log.critical('Unpack destination does not exist: {0}'.format(self.destination))

        self.log.info('Unpacking {0}'.format(self.source))
        res = self.remote_host.execute_remote(self.command)

        if not res.succeeded:
            self.log.critical('Unpack failed: {0}'.format(res))

        return res.succeeded
