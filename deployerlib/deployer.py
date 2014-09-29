import os

from deployerlib.service import Service
from deployerlib.remoteversions import RemoteVersions
from deployerlib.uploader import Uploader
from deployerlib.unpacker import Unpacker
from deployerlib.restarter import Restarter
from deployerlib.symlink import SymLink

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class Deployer(object):
    """Manage stages of deployment"""

    def __init__(self, args, config):
        self.log = Log(self.__class__.__name__)

        self.args = args
        self.config = config

        self.services = self.get_services()
        self.steps = self.get_steps(config.steps)

        if not args.redeploy and set(['upload', 'unpack', 'activate']).intersection(config.steps):
            self.get_matrix()

    def get_services(self):

        services = []

        if self.args.component:
            self.log.info('Adding service {0}'.format(self.args.component))
            services.append(Service(self.args.component, self.args, self.config))

        elif self.args.directory:

            if not os.path.isdir(self.args.directory):
                raise DeployerException('Not a directory: {0}'.format(self.args.directory))

            for filename in os.listdir(self.args.directory):
                fullpath = os.path.join(self.args.directory, filename)
                self.log.info('Adding service: {0}'.format(fullpath))
                services.append(Service(fullpath, self.args, self.config))

        else:
            raise DeployerException('Invalid configuration: no components to deploy')

        return services

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

    def get_matrix(self):
        """Determine which hosts need to be touched"""

        remoteversions = RemoteVersions(self.args, self.config, self.services)

        for service in self.services:
            need_upgrade = remoteversions.get_hosts_not_running_version(service.servicename, service.version)

            if need_upgrade != service.hosts:
                self.log.debug('Modifying deployment list for {0}'.format(service.servicename))
                service.hosts = list(set(service.hosts).intersection(need_upgrade))

            self.log.info('{0} will be deployed to: {1}'.format(service.servicename,
              ', '.join(service.hosts)))

    def deploy(self):
        """Run the requested deployment steps"""

        for step in self.steps:
            step()

    def _step_upload(self):
        """Upload packages to destination hosts"""

        uploader = Uploader(self.services, self.args, self.config)
        uploader.upload()

    def _step_unpack(self):
        """Unpack packages on destination hosts"""

        unpacker = Unpacker(self.services, self.args, self.config)
        unpacker.unpack()

    def _step_stop(self):
        """Stop services"""

        restarter = Restarter(self.services, self.args, self.config)
        restarter.stop()

    def _step_start(self):
        """Start services"""

        restarter = Restarter(self.services, self.args, self.config)
        restarter.start()

    def _step_activate(self):
        """Activate a service using a symbolic link"""

        symlink = SymLink(self.services, self.args, self.config)
        symlink.set_target()
