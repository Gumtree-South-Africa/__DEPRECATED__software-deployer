import os

from deployerlib.command import Command


class DBMigration(Command):
    """Execute database migrations"""

    def verify(self, remote_host, source):
        return True

    def execute(self):
        self.log.info('Executing database migrations using command: {0}'.format(self.source))
        res = self.remote_host.execute_remote(self.source)

        if res.succeeded:
            self.log.debug(res)
        else:
            self.log.critical('Database migration failed: {1}'.format(res))

        return res.succeeded
