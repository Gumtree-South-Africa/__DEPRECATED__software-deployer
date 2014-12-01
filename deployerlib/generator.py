import os

from fabric.colors import green
from multiprocessing import Process, Manager

from deployerlib.log import Log
from deployerlib.jobqueue import JobQueue
from deployerlib.package import Package
from deployerlib.remotehost import RemoteHost
from deployerlib.exceptions import DeployerException


class Generator(object):
    """Provide access to elements a generator might require"""

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

    def get_remote_versions(self, packages, concurrency=10, concurrency_per_host=5):
        """Get the versions of services running on remote hosts"""

        self.log.info(green('Starting stage: Check remote service versions'))

        job_list = []

        manager = Manager()
        remote_results = manager.dict()
        self._remote_versions = manager.list()

        for package in packages:
            service_config = self.config.get_with_defaults('service', package.servicename)
            hosts = [self.get_remote_host(x, self.config.user) for x in self.config.get_service_hosts(package.servicename)]

            for host in hosts:
                procname = 'RemoteVersions({0}/{1})'.format(host.hostname, package.servicename)
                job = Process(target=self._get_remote_version, args=[package, service_config, host,
                  procname, remote_results], name=procname)
                job._host = host.hostname
                job_list.append(job)

        job_queue = JobQueue(remote_results, concurrency, concurrency_per_host)
        job_queue.append(job_list)

        job_queue.close()
        queue_result = job_queue.run()
        failed = [x for x in remote_results.keys() if not remote_results[x]]

        if failed or not queue_result:
            self.log.error('Failed stage: Check remote service versions')
        else:
            self.log.info(green('Finished stage: Check remote service versions'))

        return self._resolve_remote_versions()

    def _get_remote_version(self, package, service_config, host, procname=None, remote_results={}):
        """Method passed to JobQueue to get a remote service version"""

        res = host.execute_remote('/bin/readlink {0}'.format(os.path.join(
          service_config.install_location, package.servicename)))

        if res:
            installed_package = os.path.basename(res)
            remote_version = package.get_version_from_packagename(installed_package)
        else:
            remote_version = 1

        self.log.debug('Current version is {0}'.format(remote_version), tag=package.servicename)

        self._remote_versions.append((package.servicename, host.hostname, remote_version))

        remote_results[procname] = remote_version
        return remote_version

    def _resolve_remote_versions(self):
        """Create a nested dict from the manager list
           (workaround for lack of nested manager dicts)
        """

        remote_versions = {}

        for l in self._remote_versions:
            servicename, hostname, version = l

            if not servicename in remote_versions:
                remote_versions[servicename] = {}

            remote_versions[servicename][hostname] = version

        return remote_versions

    def get_remote_host(self, hostname, username=''):
        """Return a host object from a hostname"""

        match = [x for x in self._remote_hosts if x.hostname == hostname]

        if len(match) == 1:
            return match[0]
        elif len(match) > 1:
            raise DeployerException('More than one host found with hostname{0}'.format(hostname))
        else:
            host = RemoteHost(hostname, username)
            self._remote_hosts.append(host)
            return host
