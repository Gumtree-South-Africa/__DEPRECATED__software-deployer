from deployerlib.command import Command
from deployerlib.loadbalancer import LoadBalancer


class EnableLoadbalancer(Command):
    """Enable a service on a load balancer"""

    def initialize(self, lb_hostname, lb_username, lb_password, lb_service, timeout=60):
        self.timeout = timeout
        return True

    def execute(self):
        """Enable the service"""

        res = None

        with LoadBalancer(self.lb_hostname, self.lb_username, self.lb_password, self.servicename) as lb:
            res = lb.enable_service(self.lb_service, self.timeout)

        return res
