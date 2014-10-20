from deployerlib.log import Log
from deployerlib.steps import disableloadbalancer, enableloadbalancer, controlservice, movefile, symlink


class DeployAndRestart(object):
    """Meta-step that includes load balancer control, service control and service activation"""

    def __init__(self, remote_host, source, link_target, stop_command, start_command,
      lb_hostname, lb_username, lb_password, lb_service, destination=None, check_command=None, timeout=60):
        self.log = Log(self.__class__.__name__)
        self.remote_host = remote_host

        if not destination:
            destination = source

        self.substeps = [
          disableloadbalancer.DisableLoadbalancer(lb_hostname, lb_username, lb_password, lb_service),
          controlservice.ControlService(remote_host, stop_command, check_command, want_state=2, timeout=timeout),
          movefile.MoveFile(remote_host, source, destination, clobber=True),
          symlink.SymLink(remote_host, destination, link_target),
          controlservice.ControlService(remote_host, start_command, check_command, want_state=0, timeout=timeout),
          enableloadbalancer.EnableLoadbalancer(lb_hostname, lb_username, lb_password, lb_service),
        ]

    def __repr__(self):
        return '{0}(remote_host={1} substeps={2})'.format(self.__class__.__name__,
          repr(self.remote_host.hostname), repr(self.substeps))

    def execute(self, procname=None, remote_results={}):
        """Execute the sub-steps"""

        for substep in self.substeps:
            res = substep.execute()

            if not res:
                self.log.critical('{0} substep {1} failed'.format(
                  self.__class__.__name__, substep.__class__.__name__))
                remote_results[procname] = False
                return False

        remote_results[procname] = True
        return True
