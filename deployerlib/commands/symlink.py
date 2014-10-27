from deployerlib.log import Log


class SymLink(object):
    """Manage a remote symlink"""

    def __init__(self, remote_host, source, destination):
        self.log = Log(self.__class__.__name__)
        self.remote_host = remote_host
        self.source = source
        self.destination = destination

    def __repr__(self):
        return '{0}(remote_host={1}, source={2}, destination={3})'.format(self.__class__.__name__,
          repr(self.remote_host.hostname), repr(self.source), repr(self.destination))

    def execute(self, procname=None, remote_results={}):
        """Set the link target"""

        self.log.debug('Checking for an existing link {0}'.format(self.destination))
        res = self.remote_host.execute_remote('/bin/readlink {0}'.format(self.destination))

        if res.succeeded and res == self.source:
            self.log.info('Symlink is already in place: {0}'.format(self.destination))
            remote_results[procname] = True
            return True
        else:
            self.log.debug('Symlink is not yet in place: {0}'.format(self.destination))

        self.log.info('Setting symlink for {0}'.format(self.destination))
        res = self.remote_host.execute_remote('ln -sf {0} {1}'.format(
          self.source, self.destination))

        if res.failed:
            self.log.critical('Failed to symlink {0} to {1}: {2}'.format(
              self.source, self.destination, res))
            remote_results[procname] = False
            return False

        if not self.remote_host.file_exists(self.destination):
            self.log.critical('Symlink to {0} failed: {1} was not created'.format(
              self.source, self.destination))
            remote_results[procname] = False
            return False

        return res.succeeded
