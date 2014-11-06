import os

from deployerlib.log import Log


class DBMigration(object):
    """Execute database migrations"""

    def __init__(self, remote_host, servicename, source):
        self.log = Log('{0}:{1}'.format(self.__class__.__name__,servicename))
        self.servicename = servicename

        self.remote_host = remote_host
        self.source = source

    def __repr__(self):
        return '{0}(remote_host={1}, servicename={2}, source={3})'.format(self.__class__.__name__,
          repr(self.remote_host.hostname), repr(self.servicename), repr(self.source))

    def execute(self, procname=None, remote_results={}):
        """Execute the migration for a service"""

        self.log.info('Executing database migrations using command: {0}'.format(self.source))
        res = self.remote_host.execute_remote(self.source)

        if res.succeeded:
            self.log.debug(res)
        else:
            self.log.critical('Database migration for {0} failed: {1}'.format(
              self.service.servicename, res))

        remote_results[procname] = res.succeeded
        return res.succeeded
