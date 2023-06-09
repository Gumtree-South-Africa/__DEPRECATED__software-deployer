from deployerlib.command import Command
from deployerlib.commands.controlservice import ControlService
from deployerlib.commands.checkservice import CheckService


class ReloadService(Command):
    """Start a service and check to make sure it has been started successfully"""

    def initialize(self, remote_host, reload_command, check_command=None, timeout=60):

        self.controlservice = ControlService(
          remote_host=self.remote_host,
          control_command=self.reload_command,
          tag=self.tag,
        )

        if check_command:

            self.checkservice = CheckService(
              remote_host=self.remote_host,
              check_command=self.check_command,
              want_state=0,
              timeout=timeout,
              tag=self.tag,
            )

        else:
            self.checkservice = None

        return True

    def execute(self):
        self.log.info('Reloading service')

        res = self.controlservice.execute()

        if res and self.checkservice:
            res = self.checkservice.execute()

        if not res:
            self.log.critical('Failed to reload service')
        else:
            self.log.debug('Service reloaded')

        return res
