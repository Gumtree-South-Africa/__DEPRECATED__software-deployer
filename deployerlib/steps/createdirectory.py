from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class CreateDirectory(object):
    """Create a directory on a remote host"""

    def __init__(self, remote_host, source, clobber=False, config=None):
        self.log = Log(self.__class__.__name__)
        self.remote_host = remote_host
        self.source = source
        self.clobber = clobber

    def __repr__(self):
        return '{0}(remote_host={1}, source={2}, clobber={3})'.format(self.__class__.__name__,
          repr(self.remote_host.hostname), repr(self.source), repr(self.clobber))

    def execute(self, procname=None, remote_results={}):
        """Create the directory"""

        if self.remote_host.file_exists(self.source):

            if self.clobber:
                self.log.info('Removing directory {0}'.format(self.source))
                res = self.remote_host.execute_remote('rm -rf {0}'.format(self.source))

                if not res.succeeded:
                    self.log.critical('Failed to remove {0}: {1}'.format(self.source, res))
                    return res.succeeded

            else:
                self.log.info('Directory already exists: {0}'.format(self.source))
                remote_results[procname] = True
                return True

        self.log.info('Creating directory {0}'.format(self.source))
        res = self.remote_host.execute_remote('mkdir -p {0}'.format(self.source))

        if not res.succeeded:
            self.log.critical('Failed to create directory {0}: {1}'.format(self.source, res))

        remote_results[procname] = res.succeeded
        return res.succeeded
