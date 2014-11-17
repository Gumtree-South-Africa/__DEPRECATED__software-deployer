from deployerlib.command import Command
from deployerlib.loadbalancer import LoadBalancer


class EnableLoadbalancer(Command):
    """Enable a service on a load balancer"""

    def initialize(self, lb_hostname, lb_username, lb_password, lb_service,
      continue_on_fail=True, timeout=60):
        self.timeout = timeout
        return True

    def execute(self):
        """Enable the service"""

        res = None

        with LoadBalancer(self.lb_hostname, self.lb_username, self.lb_password) as lb:
            res = lb.enable_service(self.lb_service, self.timeout)

        if res:
            self.log.info('Service {0} enabled on {1}'.format(self.lb_service, self.lb_hostname))
        else:

            if continue_on_fail:
                self.log.warning('Failed to enable {0} on {1}'.format(self.lb_service, self.lb_hostname))
                return True
            else:
                self.log.critical('Failed to enable {0} on {1}'.format(self.lb_service, self.lb_hostname))
                return res

        return res
