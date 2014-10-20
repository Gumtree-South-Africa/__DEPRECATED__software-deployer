import os

from deployerlib.log import Log


class DBMigration(object):
    """Execute database migrations"""

    def __init__(self, remote_host, source):
        self.log = Log(self.__class__.__name__)

        self.remote_host = remote_host
        self.source = source

    def __repr__(self):
        return '{0}(remote_host={1}, source={2})'.format(self.__class__.__name__,
          repr(self.remote_host.hostname), repr(self.source))

    def execute(self, procname=None, remote_results={}):
        """Execute the migration for a service"""

        self.log.info('Executing database migrations')
        res = self.remote_host.execute_remote(self.source)

        if res.succeeded:
            self.log.debug(res)
        else:
            self.log.critical('Database migration for {0} failed: {1}'.format(
              self.service.servicename, res))

        remote_results[procname] = res.succeeded
        return res.succeeded
