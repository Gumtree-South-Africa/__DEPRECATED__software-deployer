import os

from fabric.colors import green
from multiprocessing import Process, Manager

from deployerlib.log import Log
from deployerlib.jobqueue import JobQueue
from deployerlib.package import Package
from deployerlib.remotehost import RemoteHost
from deployerlib.exceptions import DeployerException
from deployerlib.commands import checkdaemontools


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

    def generate(self):
        """Generators that re-use this class can provide their own generate() method"""

        return {}

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

        return packages

    def get_remote_versions(self, packages, concurrency=10, concurrency_per_host=5, abort_on_error=True):
        """Get the versions of services running on remote hosts"""

        job_list = []

        manager = Manager()
        remote_results = manager.dict()
        remote_versions = {}
        failed = []
        queue_result = True
        init_version = 'UNDETERMINED'

        for package in packages:
            service_config = self.config.get_with_defaults('service', package.servicename)

            if not service_config:
                self.log.debug('Service not found in config: {0}'.format(package.servicename))
                continue

            if hasattr(service_config, 'enabled_on_hosts') and service_config.enabled_on_hosts == 'none' and not self.config.force:
                self.log.debug('Service disabled in config', tag=package.servicename)
                continue

            hosts = [self.get_remote_host(x, self.config.user) for x in self.config.get_service_hosts(package.servicename)]

            remote_versions_init = {}
            for host in hosts:
                remote_versions_init.update({host.hostname: init_version})
            remote_versions.update({package.servicename: remote_versions_init})

            for host in hosts:
                procname = '{0}/{1}'.format(host.hostname, package.servicename)
                job = Process(target=self._get_remote_version, args=[package, service_config, host,
                  procname, remote_results], name=procname)
                job._host = host.hostname
                job_list.append(job)


        self.log.info(green('Starting stage: Check remote service versions'))
        job_queue = JobQueue(remote_results, concurrency, concurrency_per_host, abort_on_error=abort_on_error)
        job_queue.append(job_list)

        job_queue.close()
        queue_result = job_queue.run()

        # Update remote_versions dict with actual versions from remote_results
        for item in remote_results.keys():
            ver = remote_results[item]
            host_service = item.split('/')
            remote_versions[host_service[1]].update( { host_service[0]: ver } )

        failed = [x for x in remote_results.keys() if not remote_results[x]]

        if failed or not queue_result:
            self.log.error('Failed stage: Check remote service versions')
            #raise DeployerException('Failed stage: Check remote service versions')
        else:
            self.log.info(green('Finished stage: Check remote service versions'))

        if (failed or not queue_result) and abort_on_error:
            return None
        else:
            return remote_versions

    def _get_remote_version(self, package, service_config, host, procname=None, remote_results={}):
        """Method passed to JobQueue to get a remote service version"""

        remote_version = 'NOT_INSTALLED'

        if hasattr(service_config, 'control_type') and service_config.control_type == 'props' and hasattr(service_config, 'properties_location'):
            res = host.execute_remote("/bin/cat %s/properties_version" % service_config.properties_location)

            if res:
                remote_version = res
        else:
            res = host.execute_remote('/bin/readlink {0}'.format(package.get_link_path(service_config.install_location)))

            if res:
                installed_package = package.get_packagename_from_path(res)
                remote_version = package.get_version_from_packagename(installed_package)
            else:
                checkdaemontools_command = checkdaemontools.CheckDaemontools(
                        remote_host=host,
                        servicename=package.servicename,
                        check_registered=True,
                        tag=package.servicename,
                        )
                if not checkdaemontools_command.execute():
                    remote_version += '_NOT_IN_DAEMONTOOLS'

        self.log.hidebug('Result: {0}, {1}, {2}, {3}'.format(res, res.failed, res.succeeded, res.return_code))
        self.log.info('Current version is {0}'.format(remote_version), tag=package.servicename)

        remote_results[procname] = remote_version
        return remote_version

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
        """Return a task for send_graphite"""

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
