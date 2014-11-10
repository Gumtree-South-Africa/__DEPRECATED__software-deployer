from deployerlib.command import Command


class ExecuteCommand(Command):
    """Execute a remote command"""

    def verify(self, remote_host, command):
        return True

    def execute(self):
        self.log.info('Executing command: {0}'.format(self.command))
        res = self.remote_host.execute_remote(self.command)

        if res.failed:
            self.log.critical('Failed to execute command: {0}'.format(res))

        self.log.debug('Command output: {0}'.format(res))

        return res.succeeded
