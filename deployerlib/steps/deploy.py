
from deployerlib.log import Log


class Deploy(object):
    """Meta-step that includes load balancer control, service control and service activation"""

    def __init__(self, host, servicename):
        self.log = Log(self.__class__.__name__)
        self.host = host
        self.servicename = servicename

    def execute(self):
        pass
