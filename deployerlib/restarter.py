import os

from deployerlib.log import Log
from deployerlib.fabrichelper import FabricHelper
from deployerlib.exceptions import DeployerException


class Restarter(object):
    """Handle remote service restarts"""

    def __init__(self, config, services):
        self.log = Log(self.__class__.__name__)

        self.fabrichelper = FabricHelper(config.general.user, config.args.parallel, caller=self.__class__.__name__)
        self.services = services

    def get_service_control(self, service, command):
        """Get a service control command"""

        if not hasattr(service, 'control_commands'):
            raise DeployerException('Service {0} does not have control commands configured'.format(service.servicename))

        if not command in service.control_commands:
            raise DeployerException('Service {0} does not have control command configured for "{1}"'.format(
              service.servicename, command))

        return service.control_commands[command]

    def _control(self, action):
        """Execute a service control action"""

        if action == 'stop':
            wanted_state = 2
        else:
            wanted_state = 0

        for service in self.services:

            if not service.hosts:
                self.log.info('Service {0} does not need to {1} on any hosts'.format(service.servicename, action))
                continue

            command = self.get_service_control(service, action)
            check_command = self.get_service_control(service, 'check')

            self.log.info('{0} {1} on hosts: {1}'.format(action, service.servicename,
              ', '.join(service.hosts)))

            self.fabrichelper.control_service(command, check_command, use_sudo=True,
              wanted_state=wanted_state, hosts=service.hosts)

    def stop(self):
        """Stop all services"""

        self._control('stop')

    def start(self):
        """Start all services"""

        self._control('start')

    def restart(self):
        """Restart all services"""

        self._control('restart')
