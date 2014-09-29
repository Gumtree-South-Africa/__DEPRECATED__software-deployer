from deployerlib.log import Log
from deployerlib.fabrichelper import FabricHelper
from deployerlib.exceptions import DeployerException


class SymLink(object):
    """Manage a remote symlink"""

    def __init__(self, services, args, config):
        self.log = Log(self.__class__.__name__)

        self.args = args
        self.config = config
        self.services = services

        self.fabrichelper = FabricHelper(self.config.general.user, pool_size=self.args.parallel)

    def __repr__(self):

        return '{0}(services={1})'.format(self.__class__.__name__, repr(self.services))

    def set_target(self):
        """Set the link target"""

        for service in self.services:

            if not service.hosts:
                self.log.info('Service {0} does not need to be activated on any hosts'.format(service.servicename))
                continue

            self.log.info('Setting symlink for {0} on {1}'.format(service.servicename, ', '.join(service.hosts)))

            res = self.fabrichelper.execute_remote('ln -sf {0} {1}'.format(service.install_destination, service.symlink_target),
              hosts=service.hosts)

            failed = [host for host in res if res[host].failed]

            if failed:
                raise DeployerException('Activate service {0} failed on hosts: {1}'.format(
                  service.servicename, ', '.join(failed)))

        return True
