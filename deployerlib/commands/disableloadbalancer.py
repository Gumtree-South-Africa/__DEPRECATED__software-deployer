from deployerlib.command import Command
from deployerlib.loadbalancer import LoadBalancer


class DisableLoadbalancer(Command):
    """Disable a service on a load balancer"""

    def initialize(self, lb_hostname, lb_username, lb_password, lb_service,
      timeout=60, continue_on_fail=True):
        self.timeout = timeout
        return True

    def execute(self):
        res = None

        with LoadBalancer(self.lb_hostname, self.lb_username, self.lb_password) as lb:
            res = lb.disable_service(self.lb_service, self.timeout)

        if res:
            self.log.info('Service {0} disabled on {1}'.format(self.lb_service, self.lb_hostname))
        else:

            if continue_on_fail:
                self.log.warning('Failed to disable {0} on {1}'.format(self.lb_service, self.lb_hostname))
                return True
            else:
                self.log.critical('Failed to disable {0} on {1}'.format(self.lb_service, self.lb_hostname))
                return res

        return res
