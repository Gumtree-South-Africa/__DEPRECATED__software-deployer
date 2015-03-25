import os

from fabric.colors import green, yellow
from multiprocessing import Process, Manager

from deployerlib.log import Log
from deployerlib.jobqueue import JobQueue
from deployerlib.package import Package
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

        return self.filter_ignored_packages(packages)

    def filter_ignored_packages(self, packages):
        """Strip packages which is in ignore_packages list/str if it exist"""

        if hasattr(self.config, 'ignore_packages'):
            not_filtered = packages
            packages = [ fp for fp in not_filtered if not fp.servicename in self.config.ignore_packages]
            ignored_packages = [ignored.servicename for ignored in (set(not_filtered) - set(packages))]
            self.log.warning('Ignored packages: {0}'.format( ", ".join(ignored_packages)))

        return packages

    def get_remote_versions(self, *args, **kwargs):
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
