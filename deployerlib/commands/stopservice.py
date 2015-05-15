from deployerlib.command import Command
from deployerlib.commands.controlservice import ControlService
from deployerlib.commands.checkservice import CheckService


class StopService(Command):
    """Stop a service and check to make sure it has been stopped successfully"""

    def initialize(self, remote_host, stop_command, check_command=None, status_command=None, kill_command=None, timeout=60):

        self.controlservice = ControlService(
          remote_host=self.remote_host,
          control_command=self.stop_command,
          status_command=self.status_command,
          kill_command=self.kill_command,
          want_state='down',
          tag=self.tag,
        )

        if check_command:

            self.checkservice = CheckService(
              remote_host=self.remote_host,
              check_command=self.check_command,
              want_state=2,
              timeout=timeout,
              tag=self.tag,
            )

        else:
            self.checkservice = None

        return True

    def execute(self):
        self.log.info('Stopping service')

        res = self.controlservice.execute()

        if res and self.checkservice:
            res = self.checkservice.execute()

        if not res:
            self.log.critical('Failed to stop service')
        else:
            self.log.debug('Service stopped')

        return res
