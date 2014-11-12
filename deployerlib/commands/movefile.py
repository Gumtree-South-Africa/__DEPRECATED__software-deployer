from deployerlib.command import Command


class MoveFile(Command):
    """Move or rename a remote file or directory"""

    def verify(self, remote_host, source, destination, clobber=True):
        """If clobber is True, remove the target file if it exists"""
        self.clobber = clobber
        return True

    def execute(self):

        if self.source == self.destination:
            self.log.info('Move {0}: source and destination are the same'.format(self.source))
            return True

        if self.remote_host.file_exists(self.destination):

            if self.clobber:
                self.log.info('Removing {0}'.format(self.destination))
                res = self.remote_host.execute_remote('/bin/rm -rf {0}'.format(self.destination))

                if res.failed or self.remote_host.file_exists(self.destination):
                    self.log.critical('Failed to remove {0}: {1}'.format(
                      self.destination, res))
                    return False

            else:
                self.log.critical('Unable to rename {0} to {1}: target already exists'.format(
                  self.source, self.destination))
                return False

        self.log.info('Renaming {0} to {1}'.format(self.source, self.destination))
        res = self.remote_host.execute_remote('mv {0} {1}'.format(self.source, self.destination))

        if res.failed:
            self.log.critical('Failed to rename {0} to {1}'.format(self.source, self.destination))

        return res.succeeded
