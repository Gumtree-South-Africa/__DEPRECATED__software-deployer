from deployerlib.command import Command


class SymLink(Command):
    """Manage a remote symlink"""

    def verify(self, remote_host, source, destination):
        return True

    def execute(self):
        self.log.debug('Checking for an existing link {0}'.format(self.destination))
        res = self.remote_host.execute_remote('/bin/readlink {0}'.format(self.destination))

        if res.succeeded and res == self.source:
            self.log.info('Symlink is already in place: {0}'.format(self.destination))
            return True
        else:
            self.log.debug('Symlink is not yet in place: {0}'.format(self.destination))

        self.log.info('Setting symlink for {0}'.format(self.destination))
        res = self.remote_host.execute_remote('ln -sf {0} {1}'.format(
          self.source, self.destination))

        if res.failed:
            self.log.critical('Failed to symlink {0} to {1}: {2}'.format(
              self.source, self.destination, res))
            return False

        if not self.remote_host.file_exists(self.destination):
            self.log.critical('Symlink to {0} failed: {1} was not created'.format(
              self.source, self.destination))
            return False

        return res.succeeded
