from deployerlib.command import Command


class InitScript(Command):
    """Control a service using an init script"""

    def initialize(self, remote_host, action, servicename, timeout=60, force_kill=False):
        """force_kill and timeout arguments are for compatibility with other
           control types, but they do nothing here.
        """

        if not action in ['start', 'stop', 'restart']:
            self.log.critical('{0}: Method {1} is not implemented'.format(self.__class__.__name__, action))
            return False

        return True

    def execute(self):

        command = '/etc/init.d/{0} {1}'.format(self.servicename, self.action)

        self.log.info('{0} service'.format(self.action.title() + 'ing'))
        res = self.remote_host.execute_remote(command, use_sudo=True)

        if not res.succeeded:
            self.log.critical('Failed to control service: {0}'.format(res))
            return False

        self.log.debug('{0} service'.format(self.action.title() + 'ed'))
        return True
