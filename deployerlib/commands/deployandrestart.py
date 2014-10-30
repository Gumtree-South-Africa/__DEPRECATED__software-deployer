from deployerlib.log import Log
from deployerlib.commands import disableloadbalancer, enableloadbalancer, controlservice, movefile, symlink


class DeployAndRestart(object):
    """Meta-command that includes load balancer control, service control and service activation"""

    def __init__(self, remote_host, source, link_target, stop_command, start_command,
      lb_hostname=None, lb_username=None, lb_password=None, lb_service=None, destination=None,
      check_command=None, control_timeout=60, lb_timeout=60):
        self.log = Log(self.__class__.__name__)
        self.remote_host = remote_host

        if not destination:
            destination = source

        self.subcommands = [
          controlservice.ControlService(remote_host, stop_command, check_command, want_state=2, timeout=control_timeout),
          movefile.MoveFile(remote_host, source, destination, clobber=True),
          symlink.SymLink(remote_host, destination, link_target),
          controlservice.ControlService(remote_host, start_command, check_command, want_state=0, timeout=control_timeout),
        ]

        if lb_service:
            self.subcommands.insert(0, disableloadbalancer.DisableLoadbalancer(lb_hostname, lb_username, lb_password, lb_service, timeout=lb_timeout))
            self.subcommands.append(enableloadbalancer.EnableLoadbalancer(lb_hostname, lb_username, lb_password, lb_service, timeout=lb_timeout))

    def __repr__(self):
        return '{0}(remote_host={1} subcommands={2})'.format(self.__class__.__name__,
          repr(self.remote_host.hostname), repr(self.subcommands))

    def execute(self, procname=None, remote_results={}):
        """Execute the sub-commands"""

        for subcommand in self.subcommands:
            res = subcommand.execute()

            if not res:
                self.log.critical('{0} subcommand {1} failed'.format(
                  self.__class__.__name__, subcommand.__class__.__name__))
                remote_results[procname] = False
                return False

        remote_results[procname] = True
        return True
