import os

from deployerlib.command import Command


class DBMigration(Command):
    """Execute database migrations"""

    def initialize(self, remote_host, source, if_exists=None):
        self.if_exists = if_exists
        return True

    def execute(self):

        if self.if_exists:

            if not self.remote_host.file_exists(self.if_exists):
                self.log.info('Skipping migrations, file does not exist: {0}'.format(
                  self.if_exists))
                return True

        self.log.info('Executing database migrations')
        res = self.remote_host.execute_remote(self.source)

        if res.succeeded:
            self.log.debug(res)
        else:
            self.log.critical('Database migration failed: {0}'.format(res))

        return res.succeeded
