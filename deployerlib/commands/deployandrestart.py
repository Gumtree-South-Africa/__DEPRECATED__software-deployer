from deployerlib.command import Command
from deployerlib.commands import disableloadbalancer, enableloadbalancer, stopservice, startservice, movefile, symlink


class DeployAndRestart(Command):
    """Meta-command that includes load balancer control, service control and service activation"""

    def initialize(self, remote_host, source, destination=None, stop_command=None, start_command=None,
      link_target=None, lb_hostname=None, lb_username=None, lb_password=None, lb_service=None,
      check_command=None, control_timeout=60, lb_timeout=60):

        if not destination:
            destination = source

        if lb_service:

            lb_args = {
              'lb_hostname': lb_hostname,
              'lb_username': lb_username,
              'lb_password': lb_password,
              'lb_service': lb_service,
              'timeout': lb_timeout,
              'tag': self.tag,
            }

        else:
            lb_args = None

        self.subcommands = []

        if stop_command:

            if lb_args:
                self.subcommands.append(disableloadbalancer.DisableLoadbalancer(**lb_args))

            self.subcommands.append(stopservice.StopService(
              remote_host=remote_host,
              stop_command=stop_command,
              check_command=check_command,
              timeout=control_timeout,
              tag=self.tag,
            ))

        self.subcommands.append(movefile.MoveFile(
          remote_host=remote_host,
          source=source,
          destination=destination,
          clobber=True,
          tag=self.tag,
        ))

        if link_target:

            self.subcommands.append(symlink.SymLink(
              remote_host=remote_host,
              source=destination,
              destination=link_target,
              tag=self.tag,
            ))

        if start_command:

            self.subcommands.append(startservice.StartService(
              remote_host=remote_host,
              tag=self.tag,
              start_command=start_command,
              check_command=check_command,
              timeout=control_timeout,
            ))

            if lb_args:
                self.subcommands.append(enableloadbalancer.EnableLoadbalancer(**lb_args))

        return True

    def __repr__(self):
        return '{0}(remote_host={1} tag={2})'.format(self.__class__.__name__,
          repr(self.remote_host.hostname), repr(self.tag))

    def execute(self):
        """Execute the sub-commands"""

        for subcommand in self.subcommands:
            res = subcommand.execute()

            if not res:
                self.log.critical('{0} subcommand {1} failed'.format(
                  self.__class__.__name__, subcommand.__class__.__name__))
                return False

        return True
