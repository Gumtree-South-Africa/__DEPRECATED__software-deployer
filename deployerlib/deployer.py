import os

from deployerlib.service import Service
from deployerlib.remoteversions import RemoteVersions
from deployerlib.uploader import Uploader
from deployerlib.unpacker import Unpacker
from deployerlib.loadbalancer import LoadBalancer
from deployerlib.restarter import Restarter
from deployerlib.symlink import SymLink

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class Deployer(object):
    """Manage stages of deployment"""

    def __init__(self, config):
        self.log = Log(self.__class__.__name__)

        self.config = config

        self.services = self.get_services()
        self.steps = self.get_steps(config.steps)
        self.tasks = []

#        # steps that require interaction with remote hosts
#        if not config.args.redeploy and set(['upload', 'unpack', 'activate']).intersection(config.steps):
#            self.get_matrix()

    def get_services(self):
        """Get the list of services to deploy"""

        services = []

        if self.config.args.component:

            for filename in self.config.args.component:
                self.log.info('Adding service {0}'.format(filename))
                services.append(Service(self.config, filename))

        elif self.config.args.directory:

            if not os.path.isdir(self.config.args.directory):
                raise DeployerException('Not a directory: {0}'.format(self.config.args.directory))

            for filename in os.listdir(self.config.args.directory):
                fullpath = os.path.join(self.config.args.directory, filename)
                self.log.info('Adding service: {0}'.format(fullpath))
                services.append(Service(self.config, fullpath))

        else:
            raise DeployerException('Invalid configuration: no components to deploy')

        return services

    def get_loadbalancers(self):
        """Get load balancers associated with each service"""

        self.lb = []

        for dc in self.config.datacenters:

            if not 'loadbalancers' in self.config[dc]:
                self.log.debug('No load balancers in {0}'.format(dc))
                continue

            for loadbalancer in self.config[dc]['loadbalancers']:
                self.log.debug('Logging in to LB {0}'.format(loadbalancer))

                self.lb.append(LoadBalancer(loadbalancer, self.config[dc]['loadbalancers'][loadbalancer]['username'],
                  self.config[dc]['loadbalancers'][loadbalancer]['password']))

    def logout_loadbalancers(self):
        """Log out of all load balancers"""

        for lb in self.lb:
            lb.logout()

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

#    def get_matrix(self):
#        """Determine which hosts need to be touched"""
#
#        remoteversions = RemoteVersions(self.config, self.services)
#
#        for service in self.services:
#            need_upgrade = remoteversions.get_hosts_not_running_version(service.servicename, service.version)
#
#            if need_upgrade != service.hosts:
#                self.log.debug('Modifying deployment list for {0}'.format(service.servicename))
#                service.hosts = list(set(service.hosts).intersection(need_upgrade))
#
#            self.log.info('{0} will be deployed to: {1}'.format(service.servicename,
#              ', '.join(service.hosts)))

    def deploy(self):
        """Run the requested deployment steps"""

        # test running single-threaded
        for step in self.steps:
            for service in self.services:
                for host in service.hosts:
                    step(service, host)


        if hasattr(self, 'lb'):
            self.logout_loadbalancers()

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
