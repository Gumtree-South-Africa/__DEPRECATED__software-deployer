from deployerlib.command import Command


class RemoveFile(Command):
    """Remove a file or directory"""

    def initialize(self, remote_host, source):
        return True

    def execute(self, procname=None, remote_results={}):
        """Remove the file or directory"""

        self.log.info('Removing file: {0}'.format(self.source))
        res = self.remote_host.execute_remote('rm -rf {0}'.format(self.source))

        if res.succeeded:
            self.log.debug('Removed {0}'.format(self.source))
        else:
            self.log.critical('Failed to remove {0}: {1}'.format(self.source, res))

        if self.remote_host.file_exists(self.source):
            self.log.critical('Failed to remove {0}: File still exists after removal'.format(
              self.source))
            return False

        return res.succeeded
