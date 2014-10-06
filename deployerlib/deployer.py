import os

from deployerlib.uploader import Uploader
from deployerlib.unpacker import Unpacker
#from deployerlib.loadbalancer import LoadBalancer
from deployerlib.restarter import Restarter
from deployerlib.symlink import SymLink

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class Deployer(object):
    """Manage stages of deployment"""

    def __init__(self, config, service, host):
        self.log = Log(self.__class__.__name__)

        self.config = config
        self.service = service
        self.host = host

        self.steps = self.get_steps(config.steps)

    def get_steps(self, steps):
        """Verify the list of steps to be run for deployment"""

        callables = []

        for step in steps:
            method_name = '_step_{0}'.format(step)

            if hasattr(self, method_name):
                callables.append(getattr(self, method_name))
            else:
                raise DeployerException('Unknown deployment step: {0}'.format(step))

        return callables

    def deploy(self):
        """Run the requested deployment steps"""

        self.log.info('Deploying {0} to {1}'.format(self.service, self.host))

        for step in self.steps:
            step(self.service, self.host)

    def _step_upload(self, service, host):
        """Upload packages to destination hosts"""

        uploader = Uploader(self.config, service, host)
        uploader.upload()

    def _step_unpack(self, service, host):
        """Unpack packages on destination hosts"""

        unpacker = Unpacker(self.config, service, host)
        unpacker.unpack()

    def _step_stop(self, service, host):
        """Stop services"""

        restarter = Restarter(self.config, service, host)
        restarter.stop()

    def _step_start(self, service, host):
        """Start services"""

        restarter = Restarter(self.config, service, host)
        restarter.start()

    def _step_activate(self, service, host):
        """Activate a service using a symbolic link"""

        symlink = SymLink(self.config, service, host)
        symlink.set_target()
