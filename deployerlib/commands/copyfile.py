from deployerlib.log import Log


class CopyFile(object):
    """Copy a remote file or directory to another location on the same remote host"""

    def __init__(self, remote_host, source, destination, remove_if_exists=False, continue_if_exists=False):
        """If clobber is True, remove the target file if it exists"""

        self.log = Log(self.__class__.__name__)

        self.remote_host = remote_host
        self.source = source
        self.destination = destination
        self.remove_if_exists = remove_if_exists
        self.continue_if_exists = continue_if_exists

    def __repr__(self):
        return '{0}(remote_host={1}, source={2}, destination={3})'.format(self.__class__.__name__,
          repr(self.remote_host.hostname), repr(self.source), repr(self.destination))

    def execute(self, procname=None, remote_results={}):
        """Rename a remote file or directory"""

        if self.source == self.destination:
            self.log.info('Copy {0}: source and destination are the same'.format(self.source))
            remote_results[procname] = True
            return True

        if self.remote_host.file_exists(self.destination):

            if self.remove_if_exists:
                self.log.info('Removing {0}'.format(self.destination))
                res = self.remote_host.execute_remote('/bin/rm -rf {0}'.format(self.destination))

                if res.failed or self.remote_host.file_exists(self.destination):
                    self.log.critical('Failed to remove {0}: {1}'.format(
                      self.destination, res))
                    remote_results[procname] = False
                    return False

            elif not self.continue_if_exists:
                self.log.critical('Failed to copy {0} to {1}: Destination already exists'.format(
                  self.source, self.destination))
                remote_results[procname] = False
                return False

        self.log.info('Copying {0} to {1}'.format(self.source, self.destination))
        res = self.remote_host.execute_remote('cp -Rp {0} {1}'.format(self.source, self.destination))

        if res.failed:
            self.log.critical('Failed to copy {0} to {1}'.format(self.source, self.destination))

        remote_results[procname] = res.succeeded
        return res.succeeded
