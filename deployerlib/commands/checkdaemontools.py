import os

from deployerlib.command import Command


class CheckDaemontools(Command):
    """Ensure daemontools service is configured for a service"""

    def initialize(self, remote_host, servicename, path='/var/lib/supervise'):
        self.path = path
        return True

    def execute(self):

        if not self.remote_host.file_exists(self.path):
            self.log.warning('Supervisor path does not exist: {0}'.format(self.path))
            return False

        service_path = os.path.join(self.path, self.servicename)

        if not self.remote_host.file_exists(service_path):
            self.log.warning('Service is not in daemontools')
            return False

        self.log.debug('Daemontools is enabled for this service')
        return True
