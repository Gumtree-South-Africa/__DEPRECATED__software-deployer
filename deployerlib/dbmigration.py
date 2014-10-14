import os

from deployerlib.log import Log
from deployerlib.fabrichelper import FabricHelper
from deployerlib.exceptions import DeployerException


class DBMigration(object):
    """Execute database migrations"""

    def __init__(self, config, service, host):
        self.config = config
        self.service = service
        self.host = host

        self.log = Log(self.__class__.__name__)
        self.fabrichelper = FabricHelper(self.config.general.user, host=host, caller=self.__class__.__name__)

        if not 'migration_location' in self.config.services[self.service.servicename]:
            self.log.debug('No migration_location is configured for {0}'.format(
              self.service.servicename))
        elif not 'migration_command' in self.config.services[self.service.servicename]:
            self.log.debug('No migration_command is configured for {0}'.format(
              self.service.servicename))
        else:
            self.migration_location = self.config.services[self.service.servicename]['migration_location']
            self.migration_command = self.config.services[self.service.servicename]['migration_command']

            if not self.migration_location.startswith('/'):
                self.migration_location = os.path.join(self.service.install_destination, self.migration_location)

            if 'migration_options' in self.config.services[self.service.servicename]:
                self.migration_options = self.config.services[self.service.servicename]['migration_options']
            else:
                self.migration_options = ''

    def __repr__(self):
        return '{0}(service={1}, host={2})'.format(self.__class__.__name__, self.service.servicename, self.host)

    def execute(self):
        """Execute the migration for a service"""

        if not hasattr(self, 'migration_command'):
            self.log.debug('Database migrations are not configured for {0}'.format(
              self.service.servicename))
            return True

        if not self.fabrichelper.file_exists(self.migration_location):
            self.log.info('No database migrations for {0}'.format(self.service.servicename))
            return True

        self.log.info('Executing database migrations for {0}'.format(self.service.servicename))

        command = self.migration_command.format(
          migration_location=self.migration_location,
          migration_options=self.migration_options,
        )

        res = self.fabrichelper.execute_remote(command)

        if not res.succeeded:
            self.log.critical('Database migration for {0} failed: {1}'.format(
              self.service.servicename, res))
        else:
            self.log.debug(res)

        return res.succeeded
