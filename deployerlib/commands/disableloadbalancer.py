from deployerlib.command import Command
from deployerlib.loadbalancer import LoadBalancer


class DisableLoadbalancer(Command):
    """Disable a service on a load balancer"""

    def initialize(self, lb_hostname, lb_username, lb_password, lb_service, timeout=60):
        self.timeout = timeout
        return True

    def execute(self):
        res = None

        with LoadBalancer(self.lb_hostname, self.lb_username, self.lb_password, self.tag) as lb:
            res = lb.disable_service(self.lb_service, self.timeout)

        return res
