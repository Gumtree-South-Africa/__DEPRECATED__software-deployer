from deployerlib.command import Command


class Upload(Command):
    """Upload files to a server"""

    def initialize(self, remote_host, source, destination):
        return True

    def execute(self, procname=None, remote_results={}):
        """Upload files to a server"""

        self.log.info('Uploading {0}'.format(self.source))

        res = self.remote_host.put_remote(self.source, self.destination)

        if res.succeeded:
            self.log.debug('Uploaded {0} to {1} on {2}'.format(self.source,
              self.destination, self.remote_host.hostname))

        else:
            self.log.critical('Failed to upload {0} to {1}:{2}: {3}'.format(
              self.source, self.remote_host.hostname, self.destination, res))

        return res.succeeded
