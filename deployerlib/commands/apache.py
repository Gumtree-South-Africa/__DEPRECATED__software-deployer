import time

from deployerlib.command import Command


class Apache(Command):

    def initialize(self, remote_host, action, servicename, timeout=60, force_kill=False):
        """If force_kill is specified as an option to the stop method, the kill
           method will be called if a normal stop fails.
        """

        self.timeout = timeout
        self.force_kill = force_kill

        if not hasattr(self, action):
            self.log.critical('{0}: Method {1} is not implemented'.format(self.__class__.__name__, action))
            return False

        return True

    def execute(self):
        # Run the requested action
        return getattr(self, self.action)()

    def start(self):
        """Start a Apache service"""

        command = '/usr/sbin/service apache2 start'
        self.log.info('Starting apache service')
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
        """Stop gracefully a Apache service"""

        command = '/usr/sbin/service apache2 graceful-stop'
        self.log.info('Stopping apache service')
        res = self.remote_host.execute_remote(command, use_sudo=True)

        if not res.succeeded:
            self.log.critical('Failed to control service: {0}'.format(res))
            return False

        if not self._wait('down', self.timeout):
            self.log.critical('Failed to stop service')
            return False

        self.log.debug('Successfully stopped service')
        return True

    def gc_reload(self):
        """ Gracefully reload a Apache service """

        command = '/usr/sbin/service apache2 graceful'
        self.log.info('Reloading apache service')
        res = self.remote_host.execute_remote(command, use_sudo=True)

        if not res.succeeded:
            self.log.critical('Failed to control service: {0}'.format(res))
            return False

        self.log.debug('Successfully stopped service')
        return True

    def _check_running(self):
        """Check whether a apache service is running"""

        command = '/usr/sbin/service apache2 status'.format(self.servicename)
        self.log.debug('Checking apache service: {0}'.format(command))
        res = self.remote_host.execute_remote(command, use_sudo=True)

        # Apache status return 0 if service up, and 1,2,3,n for other states, usually 3 for service down.
        state = {True: 'up', False: 'down'}
        print state.get(res.succeeded)
        return state.get(res.succeeded)

    def _check_enabled(self):
        """Check whether or not a apache service is registered"""

        res = self.remote_host.execute_remote('/usr/sbin/service apache2 status')

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
