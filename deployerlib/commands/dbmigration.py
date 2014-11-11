import os

from deployerlib.command import Command


class DBMigration(Command):
    """Execute database migrations"""

    def verify(self, remote_host, source, if_exists=None):
        self.if_exists = if_exists
        return True

    def execute(self):

        if self.if_exists:

            if not self.remote_host.file_exists(self.if_exists):
                self.log.debug('Skipping migrations for {0}, file does not exist: {1}'.format(
                  self.servicename, self.if_exists))
                return True

            self.log.debug('{0} exists, continuing with migration'.format(self.if_exists))

        self.log.info('Executing database migrations using command: {0}'.format(self.source))
        res = self.remote_host.execute_remote(self.source)

        if res.succeeded:
            self.log.debug(res)
        else:
            self.log.critical('Database migration failed: {0}'.format(res))

        return res.succeeded
