from deployerlib.command import Command


class ControlService(Command):
    """Stop, start and check a remote service"""

    def verify(self, remote_host, control_command):
        return True

    def execute(self):
        """Control and check the service"""

        self.log.debug('Controling service with: {0}'.format(self.control_command))
        res = self.remote_host.execute_remote(self.control_command, use_sudo=True)

        if not res.succeeded:
            self.log.critical('Failed to control service: {0}'.format(res))
            return False

        return True
