from deployerlib.command import Command


class ListDirectory(Command):
    """Create a directory on a remote host"""

    def initialize(self, remote_host, directory):

        return True

    def execute(self):
        """Create the directory"""

        if not self.remote_host.file_exists(self.directory):
             self.log.info('Directory {0} does not exist'.format(self.directory))
             return False
        res = self.remote_host.execute_remote('ls -1 --color=no {0}'.format(self.directory))
        if not res.succeeded:
             self.log.critical('Failed to list directory {0}: {1}'.format(self.source, res))
        self.log.info("Here are the services: \n{0}".format(res))
        return res.succeeded
