import time

from deployerlib.command import Command


class DaemonTools(Command):

    def initialize(self, remote_host, action, servicename, timeout=60, if_exists=None, unless_exists=None):
        self.timeout = timeout
        self.if_exists = if_exists
        self.unless_exists = unless_exists

        if not hasattr(self, action):
            self.log.critical('{0}: Method {1} is not implemented'.format(self.__class__.__name__, action))
            return False

        return True

    def execute(self):

        if self.if_exists and not self.remote_host.file_exists(self.if_exists):
            self.log.debug('Skipping daemontools {0}, file is not present: {1}'.format(self.action, self.if_exists))
            return True

        if self.unless_exists and self.remote_host.file_exists(self.unless_exists):
            self.log.debug('Skipping daemontools {0}, file exists: {1}'.format(self.action, self.unless_exists))
            return True

        # Run the requested action
        return getattr(self, self.action)()

    def start(self):
        command = '/usr/bin/svc -u /etc/service/{0}'.format(self.servicename)
        self.log.info('Starting daemontools service')
        res = self.remote_host.execute_remote(command, use_sudo=True)

        if not res.succeeded:
            self.log.critical('Failed to control service: {0}'.format(res))
            return False

        if not self._wait('up', self.timeout):
            self.log.critical('Failed to start service')
            return False

        self.log.debug('Successfully started service')
        return True

    def stop(self):
        command = '/usr/bin/svc -d /etc/service/{0}'.format(self.servicename)
        self.log.info('Stopping daemontools service')
        res = self.remote_host.execute_remote(command, use_sudo=True)

        if not res.succeeded:
            self.log.critical('Failed to control service: {0}'.format(res))
            return False

        if not self._wait('down', self.timeout):
            self.log.critical('Failed to stop service')
            return False

        self.log.debug('Successfully stopped service')
        return True

    def enable(self):
        """Register a daemontools service"""

        if self._check_enabled():
            self.log.debug('Service {0} is already enabled'.format(self.servicename))
            return True

        command = '/usr/sbin/update-service --add /var/lib/supervise/{0} {0}'.format(self.servicename)
        res = self.remote_host.execute_remote(command, use_sudo=True)

        if not self._check_enabled():
            self.log.critical('Failed to register daemontools service {0}: {1}'.format(self.servicename, res))
            return False

        self.log.info('Enabled daemontools service {0}, sleeping for 5 seconds'.format(self.servicename))
        # The supervise process may take a few seconds to start. Sleep for 5
        # seconds to make sure there is enough time between registering the
        # service and starting it.
        time.sleep(5)
        return True

    def disable(self):
        """Unregister a daemontools service"""

        if not self._check_enabled():
            self.log.debug('Service {0} is already disabled'.format(self.servicename))
            return True

        command = '/usr/sbin/update-service --remove /var/lib/supervise/{0} {0}'.format(self.servicename)
        res = self.remote_host.execute_remote(command, use_sudo=True)

        if self._check_enabled():
            self.log.critical('Failed to unregister daemontools service {0}: {1}'.format(self.servicename, res))
            return False

        self.log.info('Disabled daemontools service {0}'.format(self.servicename))
        return True

    def _check_running(self):
        """Check whether a daemontools service is running"""

        command = '/usr/bin/svstat /etc/service/{0}'.format(self.servicename)
        self.log.debug('Checking daemontools service: {0}'.format(command))
        res = self.remote_host.execute_remote(command, use_sudo=True)

        if not res.succeeded:
            self.log.critical('Failed to check daemontools service: {0}'.format(res))
            return False

        # return first word of status (normally 'up' or 'down')
        return res.replace('/etc/service/{0}: '.format(self.servicename), '').split()[0]

    def _check_enabled(self):
        """Check whether or not a daemontools service is registered"""

        res = self.remote_host.execute_remote('/usr/sbin/update-service --list {0}'.format(self.servicename))

        state = {True: 'registered', False: 'unregistered'}
        self.log.hidebug('Service {0} is currently {1}'.format(self.servicename, state.get(res.succeeded)))

        return res.succeeded

    def _wait(self, want_state, timeout):
        """Wait for a service to enter a given state"""

        self.log.debug('Waiting {0} seconds for service to come {1}'.format(timeout, want_state))
        max_time = time.time() + timeout

        while time.time() < max_time:

            if self._check_running() == want_state:
                self.log.debug('Service is "{0}"'.format(want_state))
                return True

            time.sleep(1)

        self.log.warning('Service did not come {0} within {1} seconds'.format(want_state, timeout))
        return False
