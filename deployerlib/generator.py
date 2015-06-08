import os

from multiprocessing import Process, Manager

from deployerlib.log import Log
from deployerlib.jobqueue import JobQueue
from deployerlib.package import Package
from deployerlib.tasklist import Tasklist
from deployerlib.remotehost import RemoteHost
from deployerlib.exceptions import DeployerException
from deployerlib.executor import Executor


class Generator(object):
    """Parent class for generators

       Generators should inherit this class and override the generate() method.
       The generate() method should return a dictionary of tasks to be run by
       the Executor.

       Generators will inherit the following methods:

       self.get_packages(): Gets a list of components as specified on the command
       line and returns a list of Package objects.

       self.get_remote_versions(list_of_package_objects): Get the versions of
       packages running on remote hosts. Returns a dict of package versions,
       i.e. remote_versions[servicename][hostname]

       self.get_graphite_stage(metric_suffix): Returns a tasklist stage that
       calls the send_graphite command.
    """

    def __init__(self, config):
        self.log = Log(self.__class__.__name__)
        self.config = config
        self._remote_hosts = []
        self.remote_versions = {}

    def generate(self):
        """Generators that re-use this class can provide their own generate() method"""

        return {}

    def use_tasklist(self):
        """Use the Tasklist class with ordered base stages"""

        self.tasklist = Tasklist()
        self.deployment_matrix = {}
        self.create_base_stages()

    def use_remote_versions(self, packages):
        """Set self.remote_versions, which will be used by self.deploy_stage()"""

        self.remote_versions = self.get_remote_versions(packages)

    def get_packages(self):
        """Get a list of packages provided on the command line"""

        packages = []

        if self.config.component:

            for filename in self.config.component:
                self.log.info('Adding package {0}'.format(filename))
                packages.append(Package(filename))

        elif self.config.release:

            for directory in self.config.release:

                if not os.path.isdir(directory):
                    raise DeployerException('Not a directory: {0}'.format(directory))

                for filename in os.listdir(directory):
                    fullpath = os.path.join(directory, filename)
                    self.log.info('Adding package: {0}'.format(fullpath))
                    packages.append(Package(fullpath))

        else:
            raise DeployerException('Invalid configuration: no components to deploy')

        return self.filter_ignored_packages(packages)

    def filter_ignored_packages(self, packages):
        """Strip packages which is in ignore_packages list/str if it exist"""

        if hasattr(self.config, 'ignore_packages'):
            not_filtered = packages
            packages = [ fp for fp in not_filtered if not fp.servicename in self.config.ignore_packages]
            ignored_packages = [ignored.servicename for ignored in (set(not_filtered) - set(packages))]
            self.log.warning('Ignored packages: {0}'.format( ", ".join(ignored_packages)))

        return packages

    def create_base_stages(self):
        """Create common stages in the correct order"""

        non_deploy_settings = {
          'concurrency': self.config.non_deploy_concurrency,
          'concurrency_per_host': self.config.non_deploy_concurrency_per_host,
        }

        for stage in ['Create temp directories', 'Upload', 'Unpack', 'Send graphite start', 'Properties', 'Database migrations', 'Set daemontools state']:
            self.tasklist.create_stage(stage, pre=True)

            if not stage == 'Database migrations':
                self.tasklist.set(stage, **non_deploy_settings)

        for stage in ['Remove temp directories', 'Cleanup']:
            self.tasklist.create_stage(stage, post=True)
            self.tasklist.set(stage, **non_deploy_settings)

    def queue_base_tasks(self, package, hostname, control_type, is_properties):
        """Add preparation and cleanup stages required for package deployment"""

        service_config = self.config.get_with_defaults('service', package.servicename)
        tempdir = os.path.join(service_config.install_location, service_config.unpack_dir)

        # Pre-deploy tasks
        self.tasklist.add('Create temp directories', {
          'command': 'createdirectory',
          'remote_host': hostname,
          'remote_user': self.config.user,
          'source': tempdir,
          'clobber': True,
        })

        self.tasklist.add('Upload', {
          'command': 'upload',
          'remote_host': hostname,
          'remote_user': self.config.user,
          'source': package.fullpath,
          'destination': service_config.destination,
          'tag': package.servicename,
        })

        self.tasklist.add('Unpack', {
          'command': 'unpack',
          'remote_host': hostname,
          'remote_user': self.config.user,
          'source': os.path.join(service_config.destination, package.filename),
          'destination': os.path.join(service_config.install_location, service_config.unpack_dir),
          'tag': package.servicename,
        })

        # Post-deploy tasks
        self.tasklist.add('Remove temp directories', {
          'command': 'removefile',
          'remote_host': hostname,
          'remote_user': self.config.user,
          'source': tempdir,
        })

        self.tasklist.add('Cleanup', {
          'command': 'cleanup',
          'remote_host': hostname,
          'remote_user': self.config.user,
          'path': service_config.destination,
          'filespec': '{0}_*'.format(package.servicename),
          'keepversions': self.config.keep_versions,
          'tag': package.servicename,
        })

        # Do not clean up install_location for properties packages
        if not is_properties:

            self.tasklist.add('Cleanup', {
              'command': 'cleanup',
              'remote_host': hostname,
              'remote_user': self.config.user,
              'path': service_config.install_location,
              'filespec': '{0}_*'.format(package.servicename),
              'keepversions': self.config.keep_versions,
              'tag': package.servicename,
            })

    def deploy_stage(self, stage_name, packages, queue_base_tasks=True, only_hosts=None, is_properties=False):
        """Build a deploy task for each package
           stage_name: The name of the stage to create for these tasks
           packages: A list of package objects
           queue_base_tasks: Create the tasks that are normally required to deploy a package, such as upload, unpack, cleanup
           only_hosts: If supplied, tasks will only be created for the hosts in this list
           is_properties: Package will be deployed as properties (i.e. copy to properties_path rather than move to install_location)
           """

        self.tasklist.create_stage(stage_name, concurrency=self.config.deploy_concurrency, concurrency_per_host=self.config.deploy_concurrency_per_host)

        for package in packages:
            service_config = self.config.get_with_defaults('service', package.servicename)
            this_stage_hosts = self.config.get_service_hosts(package.servicename)

            if not package.servicename in self.deployment_matrix:
                self.deployment_matrix[package.servicename] = []

            if only_hosts:
                this_stage_hosts = [x for x in this_stage_hosts if x in only_hosts]

            for hostname in this_stage_hosts:
                # Skip this package if it's already in the deployment matrix
                if hostname in self.deployment_matrix[package.servicename]:
                    self.log.info('{0} is already deployed to {1} in another stage'.format(package.servicename, hostname))
                    continue

                # Skip this package on this host if it is already at the correct version
                if self.remote_versions.get(package.servicename):
                    if self.remote_versions[package.servicename].get(hostname) == package.version:
                        self.log.info('Service {0} is up to date on {1}, skipping'.format(package.servicename, hostname))
                        continue

                if is_properties:
                    control_type = None
                else:
                    control_type = self.get_control_type(package.servicename, hostname)

                if queue_base_tasks:
                    self.queue_base_tasks(package, hostname, control_type, is_properties)

                self.tasklist.add(stage_name, self.get_deploy_task(package, hostname, control_type, is_properties))

                # Update deployment matrix
                self.deployment_matrix[package.servicename].append(hostname)

    def properties_stage(self, packages, queue_base_tasks=True, only_hosts=None):
        """Wrapper to deploy a packages as properties"""

        self.deploy_stage('Properties', packages, queue_base_tasks, only_hosts, is_properties=True)

    def dbmigrations_stage(self, packages, properties_path, migration_path_suffix=''):
        """Add database migration tasks for the specified packages
           packages: A list of package objects
           properties_path: The path to the properties that are used by this service
           migration_path_suffix: A relative path to append to the package's unpack location
        """

        for package in packages:
            service_config = self.config.get_with_defaults('service', package.servicename)
            deploy_hosts = self.deployment_matrix.get(package.servicename)

            if not hasattr(service_config, 'migration_command'):
                self.log.debug('Service {0} does not have a migration_command, skipping DB migrations'.format(package.servicename))
                continue

            if not deploy_hosts:
                self.log.debug('Service {0} is not being deployed, skipping DB migrations'.format(package.servicename))
                continue

            hostname = deploy_hosts[0]
            unpack_location = os.path.join(service_config.install_location, service_config.unpack_dir, package.packagename)
            migration_location = os.path.join(unpack_location, migration_path_suffix).rstrip('/')
            self.log.info('Adding db migration for {0} on {1}'.format(package.servicename, hostname))

            self.tasklist.add('Database migrations', {
              'command': 'dbmigration',
              'remote_host': hostname,
              'remote_user': self.config.user,
              'source': service_config.migration_command.format(
                unpack_location=unpack_location,
                migration_location=migration_location,
                properties_location=properties_path,
                properties_path=properties_path,
              ),
              'tag': package.servicename,
              'if_exists': migration_location,
            })

    def get_control_type(self, servicename, hostname):
        """Return control_type for a service on a given host
           If the service has an attribute enabled_on_hosts which does not
           contain the given hostname (or "all"), the control_type will be set
           to None. This allows a service to be deployed to a host without
           being started.
        """

        service_config = self.config.get_with_defaults('service', servicename)
        control_type = service_config.get('control_type')

        # Do not control services that are not enabled
        if hasattr(service_config, 'enabled_on_hosts'):
            if service_config['enabled_on_hosts'] != 'all' and not hostname in service_config['enabled_on_hosts']:
                self.log.debug('{0} is not enabled on {1}'.format(servicename, hostname))
                return None

        self.log.debug('{0} is enabled on {1}: {2}'.format(servicename, hostname, control_type))
        return control_type

    def daemontools_stage(self, packages):
        """Enable or disable services in daemontools"""

        for package in packages:
            service_config = self.config.get_with_defaults('service', package.servicename)
            control_type = service_config.get('control_type')

            # Make sure this is a daemontools service
            if service_config.get('control_type') != 'daemontools':
                self.log.hidebug('Service {0} control_type is {1}, not setting daemontools state'.format(
                  package.servicename, control_type))
                continue

            for hostname in self.config.get_service_hosts(package.servicename):
                control_type = self.get_control_type(package.servicename, hostname)

                # Check whether the service is disabled on this host
                if self.get_control_type(package.servicename, hostname):
                    self.log.debug('Service {0} will be enabled on {1}'.format(package.servicename, hostname))

                    self.tasklist.add('Set daemontools state', {
                      'command': 'daemontools',
                      'action': 'enable',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'servicename': package.servicename,
                      'tag': package.servicename,
                      'unless_exists': '/etc/service/{0}'.format(package.servicename),
                    })

                else:
                    self.log.info('Service {0} will be disabled on {1}'.format(package.servicename, hostname))

                    self.tasklist.add('Set daemontools state', {
                      'command': 'daemontools',
                      'action': 'disable',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'servicename': package.servicename,
                      'tag': package.servicename,
                    })

    def graphite_stage(self, metric_suffix):
        """Return a task for send_graphite (for new generators using the Tasklist class)"""

        stage_name = 'Send graphite {0}'.format(metric_suffix)
        self.tasklist.create_stage(stage_name)

        self.tasklist.add(stage_name, {
          'command': 'send_graphite',
          'carbon_host': self.config.get_full_hostname(self.config.graphite.carbon_host),
          'metric_name': '.'.join((self.config.graphite.metric_prefix, metric_suffix)),
        })

    def get_remote_versions(self, *args, **kwargs):
        """Get the versions of all services running on remote hosts"""

        tasks = []
        manager = Manager()
        remote_versions = manager.dict()

        for host in self.config.get_all_hosts():
            tasks.append({
              'command': 'getremoteversions',
              'remote_host': host,
              'remote_user': self.config.user,
              'install_location': self.config.service_defaults.install_location,
              'remote_versions': remote_versions,
              'properties_defs': self.config.get_all_properties(),
            })

        stage = {
          'name': 'GetRemoteVersions',
          'concurrency': self.config.non_deploy_concurrency,
          'tasks': tasks,
        }

        tasklist = {
          'name': 'Get Remote Versions',
          'stages': [stage],
        }

        executor = Executor(tasklist=tasklist)
        executor.run()
        results = {}
        # pre populate the results with empty sets
        for service in self.config.service:
            results[service] = {}
        for item in remote_versions.keys():
            ver = remote_versions[item]
            host_service = item.split('/')
            host_string = host_service[0]
            service_string = host_service[1]
            if service_string in results.keys():
                results[service_string][host_string]= ver
        return results

    def get_remote_host(self, hostname, username=''):
        """Return a host object from a hostname"""

        match = [x for x in self._remote_hosts if x.hostname == hostname]

        if len(match) == 1:
            return match[0]
        elif len(match) > 1:
            raise DeployerException('More than one host found with hostname {0}'.format(hostname))
        else:
            host = RemoteHost(hostname, username)
            self._remote_hosts.append(host)
            return host

    def get_graphite_stage(self, metric_suffix):
        """Return a task for send_graphite (for generators not using the Tasklist class)"""

        task = {
          'command': 'send_graphite',
          'carbon_host': self.config.get_full_hostname(self.config.graphite.carbon_host),
          'metric_name': '.'.join((self.config.graphite.metric_prefix, metric_suffix)),
        }

        stage = {
          'name': 'Send graphite {0}'.format(metric_suffix),
          'concurrency': 1,
          'tasks': [task],
        }

        return stage

    def get_pipeline_notify_stage(self, status, release):
        """Return a task for pipeline_notify"""

        envt = self.config.environment
        if envt == "production":
            envt = "prod"

        url = '%s/%s/%s/%s' % (self.config.pipeline_url, status, envt, release)
        if 'proxy' in self.config:
            proxy = self.config.proxy
        else:
            proxy = ''

        task = {
          'command': 'pipeline_notify',
          'url': url,
          'proxy': proxy
        }

        stage = {
          'name': 'Notify pipeline with url {0}'.format(repr(url)),
          'concurrency': 1,
          'tasks': [task],
        }

        return stage

    def get_pipeline_upload_stage(self, release):
        """Return a task for pipeline_upload"""

        url = '%s/package/%s/projects' % (self.config.pipeline_url, release)

        if 'proxy' in self.config:
            proxy = self.config.proxy
        else:
            proxy = ''

        if 'deploy_package_basedir' in self.config:
            deploy_package_basedir = self.config.deploy_package_basedir
        else:
            deploy_package_basedir = '/opt/deploy_packages'

        task = {
          'command': 'pipeline_upload',
          'deploy_package_basedir': deploy_package_basedir,
          'release': release,
          'url': url,
          'proxy': proxy
        }

        stage = {
          'name': 'Upload projects of {0} to pipeline'.format(repr(release)),
          'concurrency': 1,
          'tasks': [task],
        }

        return stage

    def get_archive_stage(self):
        """Return a task for handling the history of releases/hotfixes in the archive"""

        if hasattr(self.config, 'history'):
            history = self.config.history
        else:
            self.log.debug('No history config found. Not adding an archive stage')
            return {}

        if self.config.release and (self.config.categories or self.config.hosts or self.config.hostgroups):
            self.log.debug('Not adding an archive stage, because categories (cluster), hosts, or hostgroups was supplied')
            return {}

        task = {
          'command': 'archive',
          'archivedir': history.archivedir,
          'archivedepth': history.depth,
          'release': self.config.release,
          'components': self.config.component,
        }

        stage = {
          'name': 'Archive',
          'concurrency': 1,
          'tasks': [task],
        }

        return stage

    def get_deploy_task(self, package, hostname, control_type=None, is_properties=False):
        """Build a deploy task for a single package
           control_type: If specified, service and LB control tasks will be added
           is_properties: If specified, the service will be deployed as a properties package
        """

        service_config = self.config.get_with_defaults('service', package.servicename)

        # Begin with steps to move directory into place and create symlink
        if is_properties:
            subtasks = self._deploy_subtask_move_properties(hostname, package)
        else:
            subtasks = self._deploy_subtask_move(hostname, package)

        if not control_type:
            self.log.hidebug('Service {0} will not be controlled on {1}'.format(package.servicename, hostname))
            return subtasks

        # Add steps to stop/start the service
        stop_tasks, start_tasks = self._deploy_subtask_svc_control(hostname, package, control_type)
        subtasks = stop_tasks + subtasks + start_tasks

        # Add stops to disable/enable LB service if LB configuration is present
        if not self.config.ignore_lb:
            disable_tasks, enable_tasks = self._deploy_subtask_lb_control(hostname, package)
            subtasks = disable_tasks + subtasks + enable_tasks

        return subtasks

    def _deploy_subtask_move_properties(self, hostname, package):
        """Copy properties from the unpack directory into properties_path"""

        service_config = self.config.get_with_defaults('service', package.servicename)

        return [
          {
            'command': 'copyfile',
            'remote_host': hostname,
            'remote_user': self.config.user,
            'source': '{0}/*'.format(os.path.join(service_config.install_location,
            service_config.unpack_dir, package.packagename, service_config.environment)),
            'destination': '{0}/'.format(service_config.properties_path),
            'continue_if_exists': True,
            'tag': package.servicename,
          }
        ]

    def _deploy_subtask_move(self, hostname, package):
        """Minimum deploy consists of moving a directory into place and creating a symlink"""

        service_config = self.config.get_with_defaults('service', package.servicename)

        return [
          {
            'command': 'movefile',
            'remote_host': hostname,
            'remote_user': self.config.user,
            'tag': package.servicename,
            'source': os.path.join(service_config.install_location, service_config.unpack_dir, package.packagename),
            'destination': os.path.join(service_config.install_location, package.packagename),
            'clobber': True,
          },
          {
            'command': 'symlink',
            'remote_host': hostname,
            'remote_user': self.config.user,
            'tag': package.servicename,
            'source': os.path.join(service_config.install_location, package.packagename),
            'destination': os.path.join(service_config.install_location, package.servicename),
          },
        ]

    def _deploy_subtask_svc_control(self, hostname, package, control):
        """Steps to stop, start and check a daemontools service"""

        service_config = self.config.get_with_defaults('service', package.servicename)

        control_task = {
          'command': control,
          'remote_host': hostname,
          'remote_user': self.config.user,
          'tag': package.servicename,
          'servicename': package.servicename,
        }

        check_task = {
          'command': 'check_service',
          'remote_host': hostname,
          'remote_user': self.config.user,
          'tag': package.servicename,
          'check_command': service_config['check_command'].format(servicename=package.servicename, port=service_config['port']),
        }

        # Add optional values
        if hasattr(service_config, 'control_timeout'):
            check_task['timeout'] = service_config['control_timeout']

        # Return a tuple of tasks for stopping and tasks for starting
        stop_tasks = [
          dict(control_task.items() + [('action', 'stop')]),
          dict(check_task.items() + [('want_state', 2)]),
        ]

        start_tasks = [
          dict(control_task.items() + [('action', 'start')]),
          dict(check_task.items() + [('want_state', 0)]),
        ]

        return stop_tasks, start_tasks

    def _deploy_subtask_lb_control(self, hostname, package):
        """Steps to disable and enable a load balancer service"""

        lb_hostname, lb_username, lb_password = self.config.get_lb(package.servicename, hostname)
        service_config = self.config.get_with_defaults('service', package.servicename)
        lb_service = self.config.get_lb_servicename(package.servicename, hostname, service_config.get('lb_service'))

        # Check whether we have enough config information to do LB control
        if not (lb_hostname and lb_username and lb_password and lb_service):
            self.log.warning('No load balancer found for service on {0}'.format(hostname), tag=package.servicename)
            return [], []

        lb_task = {
          'lb_hostname': lb_hostname,
          'lb_username': lb_username,
          'lb_password': lb_password,
          'lb_service': lb_service,
          'tag': package.servicename,
        }

        if hasattr(service_config, 'lb_timeout'):
            lb_task['timeout'] = service_config['lb_timeout']

        enable_tasks = [dict(lb_task.items() + [('command', 'disable_loadbalancer')])]
        disable_tasks = [dict(lb_task.items() + [('command', 'enable_loadbalancer')])]

        return enable_tasks, disable_tasks
