import os

from itertools import izip_longest
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
        self.tasklist = Tasklist()
        self.deployment_matrix = {}

    def generate(self):
        """Generators that re-use this class can provide their own generate() method"""

        return {}

    def use_remote_versions(self, packages):
        """Set self.remote_versions, which will be used by self.deploy_packages()"""

        self.remote_versions = self.get_remote_versions(packages)

    def use_graphite(self):
        """Add graphite start and end stages"""

        if not hasattr(self.config, 'graphite'):
            self.log.info('Config does not contain graphite section, skipping graphite stages')
            return

        self.graphite_stage('start')
        self.graphite_stage('end')

    def use_pipeline(self, release_version, upload=False):
        """Add pipeline start, end, upload stages"""

        self.pipeline_notify('deploying', release_version)
        self.pipeline_notify('deployed', release_version)

        if upload:
            self.pipeline_upload(release_version)

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

        return self._filter_ignored_packages(packages)

    def create_base_stages(self):
        """Create common stages in the correct order"""

        non_deploy_settings = {
          'concurrency': self.config.non_deploy_concurrency,
          'concurrency_per_host': self.config.non_deploy_concurrency_per_host,
        }

        for stage in ['Pipeline notify deploying', 'Send graphite start', 'Upload', 'Create temp directories', 'Unpack', 'Properties', 'Database migrations', 'Set daemontools state']:
            self.tasklist.create_stage(stage, pre=True)

            if not stage == 'Database migrations':
                self.tasklist.set(stage, **non_deploy_settings)

        for stage in ['Send graphite end', 'Pipeline notify deployed', 'Pipeline upload', 'Remove temp directories', 'Cleanup']:
            self.tasklist.create_stage(stage, post=True)
            self.tasklist.set(stage, **non_deploy_settings)

    def queue_base_tasks(self, package, hostname, is_properties):
        """Add preparation and cleanup stages required for package deployment"""

        service_config = self.config.get_with_defaults('service', package.servicename)
        tempdir = os.path.join(service_config.install_location, service_config.unpack_dir)

        # Pre-deploy tasks
        self.tasklist.add('Create temp directories', {
          'command': 'createdirectory',
          'remote_host': hostname,
          'remote_user': self.config.user,
          'source': tempdir,
          'clobber': False,
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
        if self.config.get('remove_temp_dirs'):
            self.tasklist.add('Remove temp directories', {
              'command': 'removefile',
              'remote_host': hostname,
              'remote_user': self.config.user,
              'source': tempdir,
            })
        else:
            self.tasklist.add('Cleanup', {
                'command': 'cleanup',
                'remote_host': hostname,
                'remote_user': self.config.user,
                'path': os.path.join(service_config.install_location, service_config.unpack_dir),
                'filespec': '{0}_*'.format(package.servicename),
                'keepversions': 0,
                'exclude': 'XXXXXXX', # deliberately setting to a string that will never match
                'tag': package.servicename,
            })


        self.tasklist.add('Cleanup', {
          'command': 'cleanup',
          'remote_host': hostname,
          'remote_user': self.config.user,
          'path': service_config.destination,
          'filespec': '{0}_*'.format(package.servicename),
          'keepversions': self.config.keep_versions,
          'exclude': package.filename,
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
              'exclude': package.packagename,
              'tag': package.servicename,
            })

    def deploy_ordered_packages(self, packages, order, queue_base_tasks=True):
        """Create deploy stages for packages based on the specified order
           packages: A list of package objects
           order: A list of service names, optionally nested
        """

        servicenames = [x.servicename for x in packages]

        for service_list in self._sort_services(servicenames, order):
            if not service_list:
                continue

            package_list = [x for x in packages if x.servicename in service_list]
            display_package_list = ', '.join([x.servicename for x in package_list])
            self.log.debug('Deploying a group of {0} packages: {1}'.format(len(package_list), display_package_list))
            self.deploy_packages(package_list, queue_base_tasks=queue_base_tasks)

    def deploy_properties(self, packages, queue_base_tasks=True, only_hosts=None):
        """Wrapper to deploy a packages as properties"""

        self.deploy_packages(packages, 'Properties', queue_base_tasks, only_hosts, is_properties=True)

    def deploy_packages(self, packages, stage_name=None, queue_base_tasks=True, only_hosts=None, is_properties=False):
        """Build a deployment stage for a list of packages
           packages: A list of package objects
           queue_base_tasks: Create the tasks that are normally required to deploy a package, such as upload, unpack, cleanup
           only_hosts: If supplied, tasks will only be created for the hosts in this list
           is_properties: Package will be deployed as properties (i.e. copy to properties_path rather than move to install_location)
        """

        # Create base stages so they run in the correct order
        if self.tasklist.is_empty():
            self.create_base_stages()

        base_stage_name = 'Deploy {0}'.format(', '.join([x.servicename for x in packages]))

        for package in packages:
            for stage_num, hostlist in enumerate(self._get_service_stages(package.servicename, package.version)):

                if only_hosts:
                    hostlist = [x for x in hostlist if x in only_hosts]

                if not hostlist:
                    self.log.debug('Skipping an empty hostlist for stage {0}'.format(stage_name or base_stage_name))
                    continue

                if stage_name:
                    this_stage_name = stage_name
                else:
                    # Give the stage a unique name based on the stage number
                    this_stage_name = base_stage_name + '|stage{0}'.format(stage_num)

                this_tasks = self._get_deploy_tasks(package, hostlist, queue_base_tasks, is_properties)

                if not this_tasks:
                    self.log.debug('No deployment tasks for {0} on {1}'.format(package.servicename, ', '.join(hostlist)))
                    continue

                self.tasklist.create_stage(this_stage_name, concurrency=self.config.deploy_concurrency, concurrency_per_host=self.config.deploy_concurrency_per_host)
                # Track the hosts being used by this stage
                self.tasklist.add_hosts(this_stage_name, hostlist)

                # Add the tasks for this package in this stage
                for task in this_tasks:
                    self.tasklist.add(this_stage_name, task)

    def dbmigrations_stage(self, packages, properties_path=None, migration_path_suffix=''):
        """Add database migration tasks for the specified packages
           This should be run after deploy_packages so that self.deployment_matrix is populated
           packages: A list of package objects
           properties_path: The path to the properties that are used by this service
           migration_path_suffix: A relative path to append to the package's unpack location
        """

        for package in packages:
            service_config = self.config.get_with_defaults('service', package.servicename)
            deploy_hosts = self.deployment_matrix.get(package.servicename)

            if not service_config.get('migration_command'):
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
                properties_location=service_config.get('properties_location'),
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

    def pipeline_notify(self, status, release_version):
        """Update pipeline with the status of a release"""

        environment = self.config.get('environment')
        if environment == 'production':
            environment = 'prod'

        url = '{0}/{1}/{2}/{3}'.format(self.config.pipeline_url, status, environment, release_version)
        stage_name = 'Pipeline notify {0}'.format(status)

        self.tasklist.create_stage(stage_name)

        self.tasklist.add(stage_name, {
          'command': 'pipeline_notify',
          'url': url,
          'proxy': self.config.get('proxy'),
        })

    def pipeline_upload(self, release_version):
        """Upload projects of a deploy_package to pipeline"""

        url = '{0}/package/{1}/projects'.format(self.config.pipeline_url, release_version)
        deploy_package_basedir = self.config.get('deploy_package_basedir', '/opt/deploy_packages')
        stage_name = 'Pipeline upload'

        self.tasklist.create_stage(stage_name)

        self.tasklist.add(stage_name, {
          'command': 'pipeline_upload',
          'deploy_package_basedir': deploy_package_basedir,
          'release': release_version,
          'url': url,
          'proxy': self.config.get('proxy'),
        })

    def archive_stage(self):
        """Add archive stage"""

        if not self.config.get('history'):
            raise DeployerException('Archive stage requires "history" section in deployer config')

        stage_name = 'Archive'
        self.tasklist.create_stage(stage_name, post=True, concurrency=self.config.non_deploy_concurrency, concurrency_per_host=self.config.non_deploy_concurrency_per_host)

        # Archive command doesn't support multipled release directories
        for release in self.config.release:

            self.tasklist.add(stage_name, {
              'command': 'archive',
              'archivedir': self.config.history.archivedir,
              'archivedepth': self.config.history.depth,
              'release': release,
            })

        # Archive command supports multiple components
        if self.config.component:

            self.tasklist.add(stage_name, {
              'command': 'archive',
              'archivedir': self.config.history.archivedir,
              'archivedepth': self.config.history.depth,
              'components': self.config.component,
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

    def get_deploy_task(self, package, hostname, control_type=None, is_properties=False):
        """Build a deploy task for a single package
           control_type: If specified, service and LB control tasks will be added
           is_properties: If specified, the service will be deployed as a properties package
        """

        # Begin with steps to move directory into place and create symlink
        if is_properties:
            subtasks = self._deploy_subtask_move_properties(hostname, package)
        else:
            subtasks = self._deploy_subtask_move(hostname, package)

        if not control_type:
            self.log.hidebug('Service {0} will not be controlled on {1}'.format(package.servicename, hostname))
            return subtasks

        # Add steps to stop/start the service
        stop_tasks, start_tasks = self._deploy_subtask_svc_control(hostname, package.servicename, control_type)
        subtasks = stop_tasks + subtasks + start_tasks

        # Add stops to disable/enable LB service if LB configuration is present
        if not self.config.ignore_lb:
            disable_tasks, enable_tasks = self._deploy_subtask_lb_control(hostname, package.servicename)
            subtasks = disable_tasks + subtasks + enable_tasks

        return subtasks

    def _filter_ignored_packages(self, packages):
        """Strip packages which is in ignore_packages list/str if it exist"""

        if hasattr(self.config, 'ignore_packages'):
            not_filtered = packages
            packages = [ fp for fp in not_filtered if not fp.servicename in self.config.ignore_packages]
            ignored_packages = [ignored.servicename for ignored in (set(not_filtered) - set(packages))]
            self.log.info('Ignored packages: {0}'.format( ", ".join(ignored_packages)))

        return packages

    def _get_service_stages(self, servicename, version=None):
        """Determine the stages required to deploy a package while satisfying min_nodes_up
           If min_nodes_up isn't specified, it will default to 0, i.e. all nodes at once
           If the hosts running the service are limited by enabled_on_hosts,
           only the enabled hosts are taken into account when distributing the
           hosts into stages
           Hosts will be evenly distributed, meaning min_nodes_up will likely
           result in hosts being divided into two equal stages
        """

        service_config = self.config.get_with_defaults('service', servicename)

        if not service_config:
            raise DeployerException('Service not found in config: {0}'.format(servicename))

        # hosts this service is installed on (limited by --hosts if specified)
        config_hosts = self.config.get_service_hosts(servicename)
        # hosts this service is enabled on (limited by --hosts if specified)
        config_enabled_hosts = service_config.get('enabled_on_hosts', 'all')
        # All hosts that are configured for this service
        all_hosts = self.config.get_service_hosts(servicename, no_restrict=True)
        # All hosts that are enabled for this service (used to determine how many nodes can be brought down at once)
        all_enabled_hosts = config_enabled_hosts

        if config_enabled_hosts == 'all':
            config_enabled_hosts = config_hosts
            all_enabled_hosts = all_hosts

        self.log.hidebug('Service configured on: {0}'.format(', '.join(all_hosts)))
        self.log.hidebug('Service deployed to: {0}'.format(', '.join(config_hosts)))
        self.log.hidebug('Service enabled on: {0}'.format(', '.join(config_enabled_hosts)))

        # check remote versions
        if version and self.remote_versions.get(servicename):
            target_hosts = [x for x in config_hosts if self.remote_versions[servicename].get(x) != version]
        else:
            target_hosts = config_hosts

        # Get a list of skipped hosts so we can show a message
        skipped_hosts = [x for x in config_hosts if not x in target_hosts]

        if not target_hosts:
            self.log.info('All hosts have {0} version {1}'.format(servicename, version))
            return []

        if skipped_hosts:
            self.log.info('The following hosts already have {0} version {1}: {2}'.format(
              servicename, version, ', '.join(skipped_hosts)))

        self.log.hidebug('{0} configured on {1} hosts, enabled on {2} hosts'.format(
          servicename, len(all_hosts), len(all_enabled_hosts)))

        # Hosts that will have the package installed and will run the service
        enabled_hosts = [x for x in target_hosts if x in config_enabled_hosts]
        # Hosts that will have the package installed but do not run the service
        disabled_hosts = [x for x in target_hosts if not x in enabled_hosts]

        # minimum number of hosts that need to be up
        min_nodes_up = service_config.get('min_nodes_up')
        self.log.hidebug('Service {0} min_nodes_up: {1}'.format(servicename, min_nodes_up))

        # Make sure min_nodes_up is specified explicitly to avoid unexpected behaviour
        if min_nodes_up is None:
            raise DeployerException('min_nodes_up is not set for {0}'.format(servicename))

        if len(all_enabled_hosts) <= min_nodes_up:
            raise DeployerException('Service {0} configured on {1} hosts, but min_nodes_up is {2}'.format(
              servicename, len(all_enabled_hosts), min_nodes_up))

        # The maximum number of enabled_hosts that can be run in a single stage
        max_nodes_down = len(all_enabled_hosts) - min_nodes_up
        self.log.debug('Service {0} max_nodes_down: {1}'.format(servicename, max_nodes_down))

        # If all enabled hosts can be deployed in a single stage
        if len(enabled_hosts) <= max_nodes_down:
            num_stages = 1
            enabled_groups = [enabled_hosts]
        # If there are more hosts than min_nodes_up will allow, break the hosts into stages
        else:
            # The number of stages required to run all of enabled_hosts with only max_nodes_down in each stage
            num_stages = len(range(0, len(enabled_hosts), max_nodes_down))
            # If there are more nodes than min_nodes_up will allow, divide them into multiple stages
            chunk_size = int(round(float(len(enabled_hosts)) / num_stages))
            # The groupings for enabled hosts distributed by chunk_size
            enabled_groups = [enabled_hosts[i:i + chunk_size] for i in range(0, len(enabled_hosts), chunk_size)]

        self.log.debug('Service {0} will be deployed in {1} stages'.format(servicename, num_stages))

        if disabled_hosts:
            # Break the list of disabled hosts into the same number of stages as enabled_groups
            disabled_chunk_size = int(round(float(len(disabled_hosts)) / num_stages))
            disabled_groups = [disabled_hosts[i:i + disabled_chunk_size] for i in range(0, len(disabled_hosts), disabled_chunk_size)]

            # Distribute the disabled hosts across all stages
            return map(lambda x, y: sorted(x + (y or [])), enabled_groups, disabled_groups)
        else:
            return sorted(enabled_groups)

    def _sort_services(self, services, deployment_order):
        """Build a list of lists of services ordered by deployment_order
           services: List of service names
           deployment_order: List of service names, optionally nested
           Returns: A list of lists of service names; each list can be deployed in parallel
        """

        # Make sure all services are listed in deployment_order
        self._verify_deployment_order(services, deployment_order)

        ordered_services = []

        for i in deployment_order:
            if type(i) == list:
                ordered_services.append([x for x in services if x in i])
            else:
                ordered_services.append([x for x in services if x == i])

        return ordered_services

    def _verify_deployment_order(self, services, deployment_order):
        """Make sure all the specified services are listed in deployment_order"""

        def recursive_find(servicename, order):
            """Helper function to recursively search deployment_order"""

            for item in order:
                if type(item) == list and recursive_find(servicename, item):
                    return True
                elif item == servicename:
                    return True

        for servicename in services:
            if not recursive_find(servicename, deployment_order):
                raise DeployerException('Service {0} not listed in deployment_order'.format(servicename))

    def _get_deploy_tasks(self, package, hostnames, queue_base_tasks, is_properties=False):
        """Build a list of tasks required to deploy a package
           Returns a list of tasks, and a list of the hosts these tasks will be run on
        """

        tasks = []

        if not package.servicename in self.deployment_matrix:
            self.deployment_matrix[package.servicename] = []

        for hostname in hostnames:

            # Skip this package if it's already in the deployment matrix
            if hostname in self.deployment_matrix.get(package.servicename, []):
                self.log.info('{0} is already deployed to {1} in another stage'.format(package.servicename, hostname))
                continue

            if is_properties:
                control_type = None
            else:
                control_type = self.get_control_type(package.servicename, hostname)

            if queue_base_tasks:
                self.queue_base_tasks(package, hostname, is_properties)

            tasks.append(self.get_deploy_task(package, hostname, control_type, is_properties))

            # Update deployment matrix
            self.deployment_matrix[package.servicename].append(hostname)

        return tasks

    def _deploy_subtask_move_properties(self, hostname, package):
        """Copy properties from the unpack directory into properties_path"""

        service_config = self.config.get_with_defaults('service', package.servicename)

        # environment might be specified per service (icas) or per platform (aurora)
        environment = service_config.get('environment')
        if not environment:
            environment = self.config.get('environment')

        # properties path might be specified as properties_path (icas) or properties_location (aurora)
        install_path = service_config.get('properties_path')
        if not install_path:
            install_path = service_config.get('properties_location')

        source_path = os.path.join(
          service_config.install_location,
          service_config.unpack_dir,
          package.packagename,
          environment,
        )

        return [
          {
            'command': 'copyfile',
            'remote_host': hostname,
            'remote_user': self.config.user,
            'source': '{0}/*'.format(source_path),
            'destination': '{0}/'.format(install_path),
            'continue_if_exists': True,
            'tag': package.servicename,
          },
          {
            'command': 'writefile',
            'remote_host': hostname,
            'remote_user': self.config.user,
            'destination': '{0}/properties_version'.format(install_path),
            'contents': package.version,
            'clobber': True,
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

    def _deploy_subtask_svc_control(self, hostname, servicename, control):
        """Steps to stop, start and check a daemontools service"""

        service_config = self.config.get_with_defaults('service', servicename)
        force_kill = service_config.get('force_kill', False)

        control_task = {
          'command': control,
          'remote_host': hostname,
          'remote_user': self.config.user,
          'tag': servicename,
          'servicename': servicename,
        }

        check_task = {
          'command': 'check_service',
          'remote_host': hostname,
          'remote_user': self.config.user,
          'tag': servicename,
          'check_command': service_config['check_command'].format(servicename=servicename, port=service_config['port']),
        }

        # Add optional values
        if hasattr(service_config, 'control_timeout'):
            check_task['timeout'] = service_config['control_timeout']

        # Return a tuple of tasks for stopping and tasks for starting
        stop_tasks = [
          dict(control_task.items() + [('action', 'stop'), ('force', force_kill)]),
          dict(check_task.items() + [('want_state', 2)]),
        ]

        start_tasks = [
          dict(control_task.items() + [('action', 'start')]),
          dict(check_task.items() + [('want_state', 0)]),
        ]

        return stop_tasks, start_tasks

    def _deploy_subtask_lb_control(self, hostname, servicename):
        """Steps to disable and enable a load balancer service"""

        lb_hostname, lb_username, lb_password = self.config.get_lb(servicename, hostname)
        service_config = self.config.get_with_defaults('service', servicename)
        lb_service = self.config.get_lb_servicename(servicename, hostname, service_config.get('lb_service'))

        # Check whether we have enough config information to do LB control
        if not (lb_hostname and lb_username and lb_password and lb_service):
            self.log.warning('No load balancer found for service on {0}'.format(hostname), tag=servicename)
            return [], []

        lb_task = {
          'lb_hostname': lb_hostname,
          'lb_username': lb_username,
          'lb_password': lb_password,
          'lb_service': lb_service,
          'tag': servicename,
        }

        if hasattr(service_config, 'lb_timeout'):
            lb_task['timeout'] = service_config['lb_timeout']

        enable_tasks = [dict(lb_task.items() + [('command', 'disable_loadbalancer')])]
        disable_tasks = [dict(lb_task.items() + [('command', 'enable_loadbalancer')])]

        return enable_tasks, disable_tasks
