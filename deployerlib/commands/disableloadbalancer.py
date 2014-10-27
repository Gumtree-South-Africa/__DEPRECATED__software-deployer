from deployerlib.loadbalancer import LoadBalancer


class DisableLoadbalancer(object):
    """Disable a service on a load balancer"""

    def __init__(self, lb_hostname, lb_username, lb_password, lb_service):
        self.lb_hostname = lb_hostname
        self.lb_username = lb_username
        self.lb_password = lb_password
        self.lb_service = lb_service

    def __repr__(self):
        return '{0}(lb_hostname={1}, lb_service={2})'.format(self.__class__.__name__,
          repr(self.lb_hostname), repr(self.lb_service))

    def execute(self, procname=None, remote_results={}):
        """Disable the service"""

        res = None

        with LoadBalancer(self.lb_hostname, self.lb_username, self.lb_password) as lb:
            res = lb.disable_service(self.lb_service)

        remote_results[procname] = res
        return res
