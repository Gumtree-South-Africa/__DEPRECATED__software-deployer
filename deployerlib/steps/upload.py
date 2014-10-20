from deployerlib.log import Log


class Upload(object):
    """Upload files to a server"""

    def __init__(self, remote_host, source, destination, config=None):
        self.log = Log(self.__class__.__name__)
        self.remote_host = remote_host
        self.source = source
        self.destination = destination

    def __repr__(self):
        return('{0}(remote_host={1}, source={2}, destination={3})'.format(
          self.__class__.__name__, repr(self.remote_host.hostname), repr(self.source), repr(self.destination)))

    def execute(self, procname=None, remote_results={}):
        """Upload files to a server"""

        self.log.info('Uploading {0} to {1}'.format(
          self.source, self.remote_host.hostname))

        res = self.remote_host.put_remote(self.source, self.destination)

        if res.succeeded:
            self.log.debug('Uploaded {0} to {1} on {2}'.format(self.source,
              self.destination, self.remote_host.hostname))

        else:
            self.log.critical('Failed to upload {0} to {1}: {2}'.format(
              self.source, self.remote_host.hostname, res))

        remote_results[procname] = res.succeeded
        return res.succeeded
