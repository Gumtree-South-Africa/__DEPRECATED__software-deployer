from deployerlib.command import Command


class WriteFile(Command):
    """Rewrite the contents of a remote file"""

    def initialize(self, remote_host, destination, contents, clobber=False):
        self.clobber = clobber
        return True

    def execute(self):

        if self.remote_host.file_exists(self.destination) and not self.clobber:
            self.log.critical('File exists: {0}'.format(self.destination))
            return False

        res = self.remote_host.execute_remote('echo "{0}" > {1}'.format(self.contents, self.destination))

        if res.succeeded:
            self.log.info('Updated {0}'.format(self.destination))
        else:
            self.log.warning('Failed to write file {0}'.format(self.destination))

        return True
