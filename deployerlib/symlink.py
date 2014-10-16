from deployerlib.log import Log
from deployerlib.fabrichelper import FabricHelper
from deployerlib.exceptions import DeployerException


class SymLink(object):
    """Manage a remote symlink"""

    def __init__(self, config, service, host):
        self.log = Log(self.__class__.__name__, config=config)

        self.config = config
        self.service = service
        self.host = host

        self.fabrichelper = FabricHelper(self.config.user, self.host, caller=self.__class__.__name__)

    def __repr__(self):
        return '{0}(service={1}, host={2})'.format(self.__class__.__name__, repr(self.service), repr(self.host))

    def set_target(self):
        """Set the link target"""

        self.log.info('Setting symlink for {0} on {1}'.format(self.service.servicename, self.host))

        res = self.fabrichelper.execute_remote('ln -sf {0} {1}'.format(
          self.service.install_destination, self.service.symlink))

        failed = [host for host in res if res[host].failed]

        if res.failed:
            self.log.critical('Activate service {0} failed on host {1}: {2}'.format(
              self.service.servicename, self.host, res))

        return res.succeeded
