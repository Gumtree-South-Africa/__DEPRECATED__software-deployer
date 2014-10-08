import os

from fabric.colors import green

from deployerlib.uploader import Uploader
from deployerlib.unpacker import Unpacker
from deployerlib.loadbalancer import LoadBalancer
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
        self.tasks = []

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

    def get_task(self, classtype, *args, **kwargs):
        """Create new or get existing task object"""

        for task in self.tasks:
            if isinstance(task, classtype):
                self.log.debug('Reusing existing {0} object'.format(classtype.__name__))
                return task

        self.log.debug('Creating new {0} object'.format(classtype.__name__))
        newobj = classtype(*args, **kwargs)
        self.tasks.append(newobj)

        return newobj

    def deploy(self, remote_results={}, procname=None):
        """Run the requested deployment steps
           remote_results is a Manager dictionary, and procname is a Process name
           These arguments are optional, and can be used to return deploy results
           to a job manager.
        """

        self.log.info(green('Deploying {0} to {1}'.format(self.service, self.host)))

        for step in self.steps:
            res = step(self.service, self.host)

            if not res:
                self.log.critical('Step "{0}" failed!'.format(step.__name__))
                remote_results[procname] = res
                return res

        self.log.info(green('Finished deploying {0} to {1}'.format(self.service, self.host)))
        remote_results[procname] = res
        return True

    def _step_upload(self, service, host):
        """Upload packages to destination hosts"""

        uploader = Uploader(self.config, service, host)
        return uploader.upload()

    def _step_unpack(self, service, host):
        """Unpack packages on destination hosts"""

        unpacker = Unpacker(self.config, service, host)
        return unpacker.unpack()

    def _step_disable_loadbalancer(self, service, host):
        """Disable a service on a load balancer"""

        if not hasattr(service, 'lb_service'):
            self.log.warning('No lb_service configured for {0}, not doing load balancer control'.format(
              service.servicename))
            return True

        lb_hostname, lb_username, lb_password = self.config.get_lb_for_host(host)

        with LoadBalancer(lb_hostname, lb_username, lb_password) as loadbalancer:
            return loadbalancer.disable_service(service.lb_service.format(hostname=self.host))

        self.log.critical('Failed to get load balancer for {0} on {1}'.format(
          service.lb_service, host))
        return False

    def _step_enable_loadbalancer(self, service, host):
        """Enable a service on a load balancer"""

        if not hasattr(service, 'lb_service'):
            self.log.warning('No lb_service configured for {0}, not doing load balancer control'.format(
              service.servicename))
            return True

        lb_hostname, lb_username, lb_password = self.config.get_lb_for_host(host)

        with LoadBalancer(lb_hostname, lb_username, lb_password) as loadbalancer:
            return loadbalancer.enable_service(service.lb_service.format(hostname=self.host))

        self.log.critical('Failed to get load balancer for {0} on {1}'.format(
          service.lb_service, host))
        return False

    def _step_stop(self, service, host):
        """Stop services"""

        restarter = Restarter(self.config, service, host)
        return restarter.stop()

    def _step_start(self, service, host):
        """Start services"""

        restarter = Restarter(self.config, service, host)
        return restarter.start()

    def _step_activate(self, service, host):
        """Activate a service using a symbolic link"""

        symlink = SymLink(self.config, service, host)
        return symlink.set_target()
