from deployerlib.command import Command


class CopyFile(Command):
    """Copy a remote file or directory to another location on the same remote host"""

    def initialize(self, remote_host, source, destination, recursive=False,
      preserve=False, remove_if_exists=False, continue_if_exists=False):
        """If clobber is True, remove the target file if it exists"""
        self.remove_if_exists = remove_if_exists
        self.continue_if_exists = continue_if_exists

        self.args = ['/bin/cp']

        if recursive:
            self.args.append('-R')

        if preserve:
            self.args.append('-p')

        return True

    def execute(self):
        """Rename a remote file or directory"""

        if self.source == self.destination:
            self.log.info('Copy {0}: source and destination are the same'.format(self.source))
            return True

        if self.remote_host.file_exists(self.destination):

            if self.remove_if_exists:
                self.log.info('Removing {0}'.format(self.destination))
                res = self.remote_host.execute_remote('/bin/rm -rf {0}'.format(self.destination))

                if res.failed or self.remote_host.file_exists(self.destination):
                    self.log.critical('Failed to remove {0}: {1}'.format(
                      self.destination, res))
                    return False

            elif not self.continue_if_exists:
                self.log.critical('Failed to copy {0} to {1}: Destination already exists'.format(
                  self.source, self.destination))
                return False

        self.log.info('Copying {0} to {1}'.format(self.source, self.destination))
        res = self.remote_host.execute_remote('{0} {1} {2}'.format(' '.join(self.args),
          self.source, self.destination))

        if res.failed:
            self.log.critical('Failed to copy {0} to {1}: {2}'.format(self.source, self.destination, res))

        return res.succeeded
