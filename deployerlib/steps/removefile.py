from deployerlib.log import Log


class RemoveFile(object):
    """Remove a file or directory"""

    def __init__(self, host, filename):
        self.log = Log(self.__class__.__name__)
        self.host = host
        self.filename = filename

    def execute(self):
        """Remove the file or directory"""

        res = self.host.execute_remote('rm -rf {0}'.format(self.filename))

        if res.succeeded:
            self.log.debug('Removed {0}'.format(self.directory))
        else:
            self.log.critical('Failed to remove {0}: {1}'.format(self.directory, res))

        return res.succeeded
