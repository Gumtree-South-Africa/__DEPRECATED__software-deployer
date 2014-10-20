from deployerlib.log import Log


class RemoveFile(object):
    """Remove a file or directory"""

    def __init__(self, remote_host, source):
        self.log = Log(self.__class__.__name__)
        self.remote_host = remote_host
        self.source = source

    def __repr__(self):
        return '{0}(remote_host={1}, source={2})'.format(self.__class__.__name__,
          repr(self.remote_host.hostname), repr(self.source))

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
            remote_results[procname] = False
            return False

        remote_results[procname] = res.succeeded
        return res.succeeded
