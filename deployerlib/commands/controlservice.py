import time

from deployerlib.command import Command


class ControlService(Command):
    """Stop, start and check a remote service"""

    def initialize(self, remote_host, control_command, status_command=None, kill_command=None, want_state=None, timeout=60):
        self.status_command = status_command
        self.kill_command = kill_command
        self.want_state = want_state
        self.timeout = timeout
        return True

    def execute(self):
        """Control and check the service"""

        self.log.debug('Controlling service with: {0}'.format(self.control_command))
        res = self.remote_host.execute_remote(self.control_command, use_sudo=True)

        if not res.succeeded:
            self.log.critical('Failed to control service: {0}'.format(res))
            return False

        # Wait for service to be down if status_command is specified
        if self.status_command and self.want_state and not self.wait(self.want_state, self.timeout):

            if self.want_state == 'down' and self.kill_command:
                self.log.warning('Service did not respond to TERM, trying KILL')
                res = self.remote_host.execute_remote(self.kill_command, use_sudo=True)

                if not self.wait('down', self.timeout):
                    self.log.critical('Failed to KILL service')
                    return False
            else:
                self.log.critical('Failed to stop service')
                return False

        return True

    def check(self):
        """Check status of a daemontools service"""

        self.log.debug('Checking daemontools service: {0}'.format(self.status_command))
        res = self.remote_host.execute_remote(self.status_command, use_sudo=True)

        if not res.succeeded:
            self.log.critical('Failed to check daemontools service: {0}'.format(res))
            return False

        # return first word of status (normally 'up' or 'down')
        if ':' in res:
            return res.split(':')[1].split()[0]

        return False

    def wait(self, want_state, timeout):
        """Wait for a daemontools service to enter a given state"""

        self.log.debug('Waiting {0} seconds for service to come {1}'.format(timeout, want_state))
        max_time = time.time() + timeout

        while time.time() < max_time:

            if self.check() == want_state:
                self.log.debug('Service is "{0}"'.format(want_state))
                return True

            time.sleep(1)

        self.log.debug('Service did not come {0} within {1} seconds'.format(want_state, timeout))
        return False
