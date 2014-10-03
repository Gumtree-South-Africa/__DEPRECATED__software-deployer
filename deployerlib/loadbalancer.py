import time

from nsnitro import NSNitro, NSService, NSNitroError, NSNitroNserrNouser, NSNitroNserrNoservice

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class LoadBalancer(object):
    """Manage connections to a single load balancer"""

    def __init__(self, hostname, username, password):
        self.log = Log(self.__class__.__name__)

        self.hostname = hostname
        self.username = username
        self.password = password

        self.connect()

    def __repr__(self):
        return '{0}(hostname={1})'.format(self.__class__.__name__, repr(self.hostname))

    def connect(self):
        """Connect to a load balancer"""

        self.nitro = NSNitro(self.hostname, self.username, self.password)

        try:
            self.nitro.login()
        except NSNitroNserrNouser as e:
            raise DeployerException('Unable to log in to {0}: {1}'.format(self.hostname, e))
        except NSNitroError as e:
            raise DeployerException('Unable to connect to {0}: {1}'.format(self.hostname, e))

        self.log.info('Logged in to LB {0}'.format(self.hostname))

    def logout(self):
        """Log out of a load balancer"""

        self.nitro.logout()
        self.log.info('Logged out from LB {0}'.format(self.hostname))

    def get_service(self, lbservice):
        """Get a loadbalancer service object from a service name"""

        service = NSService()
        service.set_name(lbservice)

        try:
            return service.get(self.nitro, service)
        except NSNitroNserrNoservice, e:
            return None

    def get_service_state(self, lbservice):
        """Get the state of the supplied host's LB service"""

        service = self.get_service(lbservice)

        return service.get_svrstate()

    def enable_service(self, lbservice):
        """Get the state of a load balancer service"""

        service = self.get_service(lbservice)

        if service.get_svrstate() == 'UP':
            return True

        NSService.enable(self.nitro, service)
        time.sleep(2)

        service = self.get_service(lbservice)

        if service.get_svrstate() != 'UP':
            raise DeployerException('Failed to enable service {0} on {1}'.format(
              lbservice, self.hostname))

        return True

    def disable_service(self, lbservice):
        """Disable a service on the load balancer"""

        service = self.get_service(lbservice)

        if service.get_svrstate() != 'UP':
            return True

        NSService.disable(self.nitro, service)
        time.sleep(2)

        service = self.get_service(lbservice)

        if service.get_svrstate() == 'UP':
            raise DeployerException('Failed to disable service {0} on {1}'.format(
              lbservice, self.hostname))

        return True
