import os

from deployerlib.service import Service
from deployerlib.fabrichelper import FabricHelper
from deployerlib.remoteversions import RemoteVersions
from deployerlib.uploader import Uploader
from deployerlib.unpacker import Unpacker
from deployerlib.symlink import SymLink

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class Deployer(object):
    """Manage stages of deployment"""

    def __init__(self, args, config):
        self.log = Log(self.__class__.__name__)

        self.args = args
        self.config = config

        general = self.config.get(['general'])

        self.services = self.get_services()
        self.fabrichelper = FabricHelper(general['user'], pool_size=self.args.parallel)

    def get_services(self):

        services = []

        if self.args.component:
            self.log.info('Adding service: {0}'.format(self.args.component))
            services.append(Service(self.args.component, self.args, self.config))

        elif self.args.directory:

            if not os.path.isdir(self.args.directory):
                self.log.critical('Not a directory: {0}'.format(self.args.directory))

            for file in os.listdir(self.args.directory):
                fullpath = os.path.join(self.args.directory, file)
                self.log.info('Adding service: {0}'.format(fullpath))
                services.append(Service(fullpath, self.args, self.config))

        else:
            raise DeployerException('Invalid configuration: no components to deploy')

        return services

    def pre_deploy(self):
        """Upload and unpack"""

        if not self.args.redeploy:
            remoteversions = RemoteVersions(self.fabrichelper, self.services)

            for service in self.services:
                need_upgrade = remoteversions.get_hosts_not_running_version(service.servicename, service.version)

                if need_upgrade != service.hosts:
                    self.log.debug('Modifying deployment list for {0}'.format(service.servicename))
                    service.hosts = list(set(service.hosts).intersection(need_upgrade))

                self.log.info('{0} will be deployed to: {1}'.format(service.servicename,
                  ', '.join(service.hosts)))

        uploader = Uploader(self)
        uploader.upload()

        unpacker = Unpacker(self)
        unpacker.unpack()

    def deploy(self):
        """Activate new version"""

        for service in self.services:
            symlink_target = os.path.join(service.install_location, service.servicename)
            symlink = SymLink(self.fabrichelper, symlink_target)
            symlink.set_target(service.install_destination, service.hosts)
