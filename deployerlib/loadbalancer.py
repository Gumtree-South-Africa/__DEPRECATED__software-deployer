import time

from nsnitro import NSNitro, NSService, NSNitroError, NSNitroNserrNouser, NSNitroNserrNoservice

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class LoadBalancer(object):
    """Manage connections to a single load balancer"""

    def __init__(self, hostname, username, password, config=None):
        self.log = Log(self.__class__.__name__)

        self.hostname = hostname
        self.username = username
        self.password = password

        self.connect()

    def __repr__(self):
        return '{0}(hostname={1})'.format(self.__class__.__name__, repr(self.hostname))

    def __enter__(self):
        """When used as a context manager"""

        return self

    def __exit__(self, *err):
        """Log out of the load balancer if the object is destroyed"""

        if hasattr(self, 'nitro'):

            try:
                self.logout()
            except NSNitroError:
                pass

    def connect(self):
        """Connect to a load balancer"""

        self.nitro = NSNitro(self.hostname, self.username, self.password)

        try:
            self.nitro.login()
        except NSNitroNserrNouser as e:
            raise DeployerException('Unable to log in to {0}: {1}'.format(self.hostname, e))
        except NSNitroError as e:
            raise DeployerException('Unable to connect to {0}: {1}'.format(self.hostname, e))

        self.log.debug('Logged in to LB {0}'.format(self.hostname))

    def logout(self):
        """Log out of a load balancer"""

        self.nitro.logout()
        self.log.debug('Logged out from LB {0}'.format(self.hostname))

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

        if not service:
            self.log.warning('No such service {0} on {1}'.format(lbservice, self.hostname))
            return None, None
        else:
            return service.get_svrstate(), service

    def enable_service(self, lbservice, timeout=60):
        """Get the state of a load balancer service"""

        cur_state, service = self.get_service_state(lbservice)

        if not service:
            self.log.warning('Service {0} does not exist on {1}'.format(lbservice, self.hostname))
            return True

        if cur_state == 'UP':
            self.log.warning('Service {0} is already {1}'.format(lbservice, cur_state))
            return True

        NSService.enable(self.nitro, service)

        maxtime = time.time() + timeout

        while time.time() < maxtime:
            time.sleep(1)

            new_state, service = self.get_service_state(lbservice)

            if new_state == 'UP':
                self.log.info('{0} is now {1} on {2}'.format(lbservice, new_state, self.hostname))
                return True

            self.log.debug('{0} is still {1} on {2}'.format(lbservice, new_state, self.hostname))

        self.log.critical('Failed to enable service {0} on {1} (state is {2}'.format(
          lbservice, self.hostname, new_state))
        return False

    def disable_service(self, lbservice, timeout=60):
        """Disable a service on the load balancer"""

        cur_state, service = self.get_service_state(lbservice)

        if not service:
            self.log.warning('Service {0} does not exist on {1}'.format(lbservice, self.hostname))
            return True

        if cur_state != 'UP':
            self.log.warning('Service {0} is already {1}'.format(lbservice, cur_state))
            return True

        NSService.disable(self.nitro, service)

        maxtime = time.time() + timeout

        while time.time() < maxtime:
            time.sleep(1)

            service = self.get_service(lbservice)
            new_state = service.get_svrstate()

            if new_state != 'UP':

                self.log.info('{0} is now {1} on {2}'.format(lbservice, new_state, self.hostname))
                return True

            self.log.debug('{0} is still {1} on {2}'.format(lbservice, new_state, self.hostname))

        self.log.critical('Failed to disable service {0} on {1} (state is {2})'.format(
          lbservice, self.hostname, new_state))
        return False
