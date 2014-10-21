import os

from fabric.colors import green

from deployerlib.steps.uploader import Uploader
from deployerlib.steps.unpacker import Unpacker
from deployerlib.steps.renamefile import RenameFile
from deployerlib.steps.dbmigration import DBMigration
from deployerlib.loadbalancer import LoadBalancer
from deployerlib.steps.restarter import Restarter
from deployerlib.steps.symlink import SymLink

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class Deployer(object):
    """Manage stages of deployment"""

    def __init__(self, config, service, host, migration_executed=None):
        self.log = Log(self.__class__.__name__)

        self.config = config
        self.service = service
        self.host = host
        self.migration_executed = migration_executed

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

    def deploy(self, remote_results=None, procname=None):
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

                if remote_results is not None:
                    remote_results[procname] = res

                return res

        self.log.info(green('Finished deploying {0} to {1}'.format(self.service, self.host)))

        if remote_results is not None:
            remote_results[procname] = res

        return True

    def _step_upload_package(self, service, host):
        """Upload packages to destination hosts"""

        uploader = Uploader(self.config, service, host)
        return uploader.upload()

    def _step_unpack_package(self, service, host):
        """Unpack packages on destination hosts"""

        unpacker = Unpacker(self.config, service, host)
        return unpacker.unpack()

    def _step_database_migrations(self, service, host):
        """Execute database migrations for a service"""

        if service.servicename in self.migration_executed:
            self.log.debug('Skipping database migrations for {0}'.format(
              service.servicename))
            return True

        dbmigration = DBMigration(self.config, service, host)
        res = dbmigration.execute()

        if res:
            self.migration_executed[service.servicename] = True

        return res

    def _do_on_loadbalancer(self, action, service, host):
        """Disable/Enable a service on a load balancer"""

        if action == 'disable':
            action_text = 'Disabling'
        elif action == 'enable':
            action_text = 'Enabling'
        else:
            raise DeployerException('Unknown loadbalancer action {0}'.format(action))

        if not hasattr(service, 'lb_service'):
            self.log.warning('No lb_service configured for {0}, not doing load balancer control'.format(
              service.servicename))
            return True

        lb_service = service.lb_service.format(hostname=host.hostname)
        lb_hostname, lb_username, lb_password = self.config.get_lb(service.servicename, host.hostname)

        if lb_hostname:
            self.log.info('{2} service "{0}" on {1}'.format(lb_service, lb_hostname, action_text))
            with LoadBalancer(lb_hostname, lb_username, lb_password) as loadbalancer:
                lb_action = eval('loadbalancer.'+action+'_service')
                return lb_action(lb_service)
        else:
            self.log.critical('Failed to get load balancer for {0} on {1}'.format(
                service.servicename, host.hostname))
            return False

    def _step_disable_loadbalancer(self, service, host):
        """Disable a service on a load balancer"""

        return self._do_on_loadbalancer('disable', service, host)

    def _step_enable_loadbalancer(self, service, host):
        """Enable a service on a load balancer"""

        return self._do_on_loadbalancer('enable', service, host)

    def _step_stop_service(self, service, host):
        """Stop services"""

        restarter = Restarter(self.config, service, host)
        return restarter.stop()

    def _step_start_service(self, service, host):
        """Start services"""

        restarter = Restarter(self.config, service, host)
        return restarter.start()

    def _step_activate_service(self, service, host):
        """Activate a service using a symbolic link"""

        if service.unpack_destination != service.install_destination:
            renamefile = RenameFile(self.config, service.unpack_destination,
              service.install_destination, host)
            renamefile.rename()

        symlink = SymLink(self.config, service, host)
        return symlink.set_target()
