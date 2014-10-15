import os
import time

from deployerlib.log import Log
from deployerlib.fabrichelper import FabricHelper
from deployerlib.exceptions import DeployerException


class Restarter(object):
    """Handle remote service restarts"""

    def __init__(self, config, service, host, timeout=60):
        self.log = Log(self.__class__.__name__)

        self.service = service
        self.host = host
        self.timeout = timeout

        self.fabrichelper = FabricHelper(config.general.user, self.host, caller=self.__class__.__name__)

    def get_service_control(self, service, command):
        """Get a service control command"""

        if not hasattr(service, 'control_commands'):
            raise DeployerException('Service {0} does not have control commands configured'.format(service.servicename))

        if not command in service.control_commands:
            raise DeployerException('Service {0} does not have control command configured for "{1}"'.format(
              service.servicename, command))

        return service.control_commands[command]

    def _control_service(self, action):
        """Execute a service control action"""

        if action == 'stop':
            wanted_state = 2
        else:
            wanted_state = 0

        control_command = self.get_service_control(self.service, action)

        self.log.info('{0} {1} on {2}'.format(action.capitalize(),
          self.service.servicename, self.host))

        res = self.fabrichelper.execute_remote(control_command, use_sudo=True)

        if res.failed:
            self.log.critical('Failed to {0} {1} on {2}: {3}'.format(action,
              self.service.servicename, self.host, res))
            return False

        return self.check_service(wanted_state)

    def check_service(self, wanted_state):
        """Probe a service to make sure it's in the correct state"""

        check_command = self.get_service_control(self.service, 'check')

        timeout = time.time() + self.timeout
        success = False

        while time.time() < timeout:
            time.sleep(1)
            res = self.fabrichelper.execute_remote(check_command)

            if res.return_code == wanted_state:
                success = True
                break

            time.sleep(1)

        msg = 'Service {0} status on {1}: {2}'.format(self.service.servicename, self.host, res)

        if success:
            self.log.info(msg)
            return True
        else:
            self.log.critical(msg)
            return False

    def stop(self):
        """Stop all services"""

        return self._control_service('stop')

    def start(self):
        """Start all services"""

        return self._control_service('start')

    def restart(self):
        """Restart all services"""

        return self._control_service('restart')
