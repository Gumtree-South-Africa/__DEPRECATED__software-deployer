import os

from fabric.colors import green
from multiprocessing import Process, Manager

from deployerlib.log import Log
from deployerlib.jobqueue import JobQueue
from deployerlib.service import Service
from deployerlib.remoteversions import RemoteVersions
from deployerlib.exceptions import DeployerException


class MatrixHelper(object):
    """Build a deployment matrix"""

    def __init__(self, config):
        self.log = Log(self.__class__.__name__)
        self.config = config

    def get_services(self):
        """Get a list of services provided on the command line"""

        services = []

        if self.config.component:

            for filename in self.config.component:
                self.log.info('Adding service {0}'.format(filename))
                services.append(Service(self.config, filename))

        elif self.config.directory:

            if not os.path.isdir(self.config.directory):
                raise DeployerException('Not a directory: {0}'.format(self.config.directory))

            for filename in os.listdir(self.config.directory):
                fullpath = os.path.join(self.config.directory, filename)
                self.log.info('Adding service: {0}'.format(fullpath))
                services.append(Service(self.config, fullpath))

        else:
            raise DeployerException('Invalid configuration: no components to deploy')

        return services

    def get_remote_versions(self, services):
        """Get the versions of services running on remote hosts"""

        self.log.info(green('Starting stage: Check remote service versions'))

        remoteversions = RemoteVersions()
        job_list = []

        manager = Manager()
        remote_results = manager.dict()

        for service in services:
            for host in service.hosts:
                procname = 'RemoteVersions({0}/{1})'.format(host.hostname, service.servicename)
                job = Process(target=remoteversions.get_remote_version, args=[service, host,
                  procname, remote_results], name=procname)
                job._host = host.hostname
                job_list.append(job)

        job_queue = JobQueue(10, remote_results=remote_results)
        job_queue.append(job_list)

        job_queue.close()
        res = job_queue.run()
        self.log.info(green('Finished stage: Check remote service versions'))

        failed = [x for x in remote_results.keys() if not remote_results[x]]

        if failed or not res:
            raise DeployerException('Failed jobs: {0}'.format(', '.join(failed)))

        return remoteversions.resolve_remote_versions()
