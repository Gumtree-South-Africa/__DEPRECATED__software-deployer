import os

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class Restarter(object):
    """Handle remote service restarts"""

    def __init__(self, fabrichelper, *services):
        self.log = Log(self.__class__.__name__)

        self.fabrichelper = fabrichelper
        self.services = services

    def get_service_control(self, service, command):
        """Get a service control command"""

        if not hasattr(service, 'control_commands'):
            raise DeployerException('Service {0} does not have control commands configured'.format(service.servicename))

        if not command in service.control_commands:
            raise DeployerException('Service {0} does not have control command configured for "{1}"'.format(
              service.servicename, command))

        return service.control_commands[command]

    def stop(self):
        """Stop all services"""

        for service in self.services:
            stop_command = self.get_service_control(service, 'stop')
            check_command = self.get_service_control(service, 'check')
            self.log.info('Stopping {0} on hosts: {1}'.format(service.servicename, ', '.join(service.hosts)))
            self.fabrichelper.control_service(stop_command, check_command, use_sudo=True, wanted_state=2, hosts=service.hosts)

    def start(self):
        """Start all services"""

        for service in self.services:
            start_command = self.get_service_control(service, 'start')
            check_command = self.get_service_control(service, 'check')
            self.log.info('Starting {0} on hosts: {1}'.format(service.servicename, ', '.join(service.hosts)))
            self.fabrichelper.control_service(start_command, check_command, use_sudo=True, hosts=service.hosts)

    def restart(self):
        """Restart all services"""

        self.stop()
        self.start()

    def refresh(self):
        """Refresh a service"""

        for service in self.services:
            command = self.get_service_control(service, 'refresh')
            self.log.info('Refreshing {0} on hosts: {1}'.format(service.servicename, ', '.join(service.hosts)))
            res = self.fabrichelper.execute_remote(command, use_sudo=True, hosts=service.hosts, warn_only=False)
