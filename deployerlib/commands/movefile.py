from deployerlib.log import Log


class MoveFile(object):
    """Move or rename a remote file or directory"""

    def __init__(self, remote_host, servicename, source, destination, clobber=True):
        """If clobber is True, remove the target file if it exists"""

        self.log = Log('{0}:{1}'.format(self.__class__.__name__,servicename))
        self.servicename = servicename

        self.remote_host = remote_host
        self.source = source
        self.destination = destination
        self.clobber = clobber

    def __repr__(self):
        return '{0}(remote_host={1}, servicename={2}, source={3}, destination={4})'.format(self.__class__.__name__,
          repr(self.remote_host.hostname), repr(self.servicename), repr(self.source), repr(self.destination))

    def execute(self, procname=None, remote_results={}):
        """Rename a remote file or directory"""

        if self.source == self.destination:
            self.log.info('Move {0}: source and destination are the same'.format(self.source))
            remote_results[procname] = True
            return True

        if self.remote_host.file_exists(self.destination):

            if self.clobber:
                self.log.info('Removing {0}'.format(self.destination))
                res = self.remote_host.execute_remote('/bin/rm -rf {0}'.format(self.destination))

                if res.failed or self.remote_host.file_exists(self.destination):
                    self.log.critical('Failed to remove {0}: {1}'.format(
                      self.destination, res))
                    remote_results[procname] = False
                    return False

            else:
                self.log.critical('Unable to rename {0} to {1}: target already exists'.format(
                  self.source, self.destination))
                remote_results[procname] = False
                return False

        self.log.info('Renaming {0} to {1}'.format(self.source, self.destination))
        res = self.remote_host.execute_remote('mv {0} {1}'.format(self.source, self.destination))

        if res.failed:
            self.log.critical('Failed to rename {0} to {1}'.format(self.source, self.destination))

        remote_results[procname] = res.succeeded
        return res.succeeded
