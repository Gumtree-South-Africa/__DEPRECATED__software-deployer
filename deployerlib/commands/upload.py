from deployerlib.log import Log


class Upload(object):
    """Upload files to a server"""

    def __init__(self, remote_host, source, destination, servicename):
        self.log = Log('{0}:{1}'.format(self.__class__.__name__,servicename))
        self.servicename = servicename
        self.remote_host = remote_host
        self.source = source
        self.destination = destination

    def __repr__(self):
        return('{0}(remote_host={1}, source={2}, destination={3}, servicename={4})'.format(
          self.__class__.__name__, repr(self.remote_host.hostname), repr(self.source), repr(self.destination), repr(self.servicename)))

    def execute(self, procname=None, remote_results={}):
        """Upload files to a server"""

        self.log.info('Uploading {0} to {1}'.format(
            self.source, '{0}:{1}'.format(self.remote_host.hostname,self.destination)))

        res = self.remote_host.put_remote(self.source, self.destination)

        if res.succeeded:
            self.log.debug('Uploaded {0} to {1} on {2}'.format(self.source,
              self.destination, self.remote_host.hostname))

        else:
            self.log.critical('Failed to upload {0} to {1}: {2}'.format(
              self.source, '{0}:{1}'.format(self.remote_host.hostname,self.destination), res))

        remote_results[procname] = res.succeeded
        return res.succeeded
