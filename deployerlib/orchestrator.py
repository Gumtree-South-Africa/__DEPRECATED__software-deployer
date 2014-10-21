import os

from Queue import Queue
from multiprocessing import Process, Manager

from deployerlib.log import Log
from deployerlib.service import Service
from deployerlib.remoteversions import RemoteVersions
from deployerlib.deployer import Deployer
from deployerlib.jobqueue import JobQueue
from deployerlib.exceptions import DeployerException


class Orchestrator(object):
    """Build deployer objects for each component to be deployed"""

    def __init__(self, config, services=[]):
        self.config = config
        self.log = Log(self.__class__.__name__)

        if services:
            self.services = services
        else:
            self.services = self.get_services()

        manager = Manager()
        self.job_results = manager.dict()
        self.migration_executed = manager.dict()

    def get_services(self):
        """Get the list of services to deploy as specified on the command line"""

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

        if hasattr(self.config, 'deployment_order'):
            services = self.sort_services(services, self.config.deployment_order)
        else:
            self.log.info('No deployment_order has been specified')

        return services

    def sort_services(self, services, order):
        """Sort a list of services according to a specified order
           services: A list of service objects to be put into order
           order: A list of servicename strings by which the services will be ordered
        """

        def _flatten(l):
            """Return a flat list from a nested list"""

            flat_list = []

            for i in l:

                if type(i) == list:
                    flat_list += _flatten(i)
                else:
                    flat_list.append(i)

            return flat_list

        order = _flatten(order)
        newlist = []

        for servicename in order:
            sortitem = next((x for x in services if x.servicename == servicename), None)

            if sortitem:
                newlist.append(sortitem)
            else:
                self.log.debug('Service {0} specified in deployment order, but there is no package to deploy'.format(servicename))

        extra_services = [x.servicename for x in services if not x in newlist]

        if extra_services:
            raise DeployerException('Services not defined in deployment_order: {0}'.format(', '.join(extra_services)))

        return newlist

    def get_remote_versions(self):
        """Get the versions of services running on remote hosts"""

        remoteversions = RemoteVersions(self.config)
        job_list = []
        self.job_results.clear()

        for service in self.services:
            for host in service.hosts:
                procname = 'RemoteVersions({0}/{1})'.format(host.hostname, service.servicename)
                job = Process(target=remoteversions.get_remote_version, args=[service, host,
                  self.job_results, procname], name=procname)
                job._host = host.hostname
                job_list.append(job)

        self._run_jobs(jobs=job_list, parallel=20)

        return remoteversions.resolve_remote_versions()

    def get_job_list(self):
        """Build a list of jobs"""

        def _need_deploy(service, host):
            """Helper function to answer whether or not a service needs to be deployed"""

            if self.config.redeploy:
                return True

            if not hasattr(self, 'remote_versions'):
                return True

            if not hasattr(service, 'version'):
                return True

            if service.servicename in self.remote_versions and host in self.remote_versions[service.servicename]:
                if self.remote_versions[service.servicename][host.hostname] == service.version:
                    return False

            return True

        job_list = []
        self.job_results.clear()

        for service in self.services:
            for host in service.hosts:

                if not _need_deploy(service, host):
                    self.log.debug('{0} is already at version {1} on {2}'.format(
                      service.servicename, service.version, host.hostname))
                    continue

                self.log.debug('{0} will be deployed to {1}'.format(service.servicename, host.hostname))

                procname = '{0}/{1}'.format(host.hostname, service.servicename)
                deployer = Deployer(self.config, service, host, self.migration_executed)
                job = Process(target=deployer.deploy, args=[self.job_results, procname], name=procname)
                job._host = host.hostname
                job._service = service.servicename
                job_list.append(job)

        return job_list

    def direct_run(self):
        """Run jobs directly and in parallel, without ordering or separation"""

        self.deploy_tasks = self.get_job_list()

        if not self.deploy_tasks:
            self.log.info('No jobs to run')
            return True

        # run remaining jobs
        self._run_jobs(self.deploy_tasks)

    def deploy_run(self):
        """Run jobs as a deployment task:
           - Start with a single host
           - Then run in parallel, following deployment_order
           - Finally run all remaining jobs in parallel
        """

        self.remote_versions = self.get_remote_versions()
        self.deploy_tasks = self.get_job_list()

        if not self.deploy_tasks:
            self.log.info('Nothing to deploy')
            return True

        # deploy to a single host
        if hasattr(self.config, 'single_host'):
            single_host = self.config.single_host

            # If there are no tasks for the configured host, use the first one we come across
            if not [x for x in self.deploy_tasks if x._host == single_host]:
                single_host = self.deploy_tasks[0]._host
                self.log.debug('No jobs in the queue for {0}, using {1} as the single_host instead'.format(
                  self.config.single_host, single_host))

            completed = self._run_jobs_for_host(self.deploy_tasks, single_host)

            # remove completed jobs from the task list
            self.deploy_tasks = [x for x in self.deploy_tasks if not x in completed]

        # run services according to the deployment_order
        if self.deploy_tasks and hasattr(self.config, 'deployment_order'):

            for servicenames in self.config.deployment_order:
                completed = self._run_jobs_for_service(self.deploy_tasks, servicenames)

                # remove completed jobs from the task list
                self.deploy_tasks = [x for x in self.deploy_tasks if not x in completed]

        # run remaining jobs
        self._run_jobs(self.deploy_tasks)

    def _run_jobs(self, jobs, parallel=None):
        """Start running a job queue"""

        if not jobs:
            self.log.info('Finished running job queue')
            return

        # By default use the parallel specified on the command line
        if not parallel:
            parallel = self.config.parallel

        queue = Queue()
        job_queue = JobQueue(parallel, queue, self.job_results)

        # add jobs to queue
        for job in jobs:
            job_queue.append(job)

        self.log.debug('Running {0} jobs with pool size {1}'.format(len(jobs), parallel))

        job_queue.close()
        res = job_queue.run()

        # check results of each job
        failed = [x for x in self.job_results.keys() if not self.job_results[x]]

        if failed:
            raise DeployerException('Failed jobs: {0}'.format(', '.join(failed)))

        return res

    def _run_jobs_for_host(self, jobs, hostnames):
        """Run all jobs for the specified hostname"""

        if not isinstance(hostnames, list):
            hostnames = [hostnames]

        run_now = [x for x in jobs if x._host in hostnames]

        if not run_now:
            self.log.debug('{0} jobs in the queue, none are destined for {1}'.format(
              len(jobs), ' or '.join(hostnames)))
            return []

        self.log.info('Queuing {0} jobs on {1}'.format(len(run_now), ', '.join(hostnames)))
        self._run_jobs(run_now, parallel=1)

        return run_now

    def _run_jobs_for_service(self, jobs, servicenames):
        """Run all jobs for the specified service"""

        if isinstance(servicenames, basestring):
            servicenames = [servicenames]

        run_now = [x for x in jobs if x._service in servicenames]

        if not run_now:
            self.log.debug('{0} jobs in the queue, but none are for service {1}'.format(
              len(jobs), ' or '.join(servicenames)))
            return []

        self.log.info('Queuing {0} jobs for service {1}'.format(len(run_now), ', '.join(servicenames)))
        self._run_jobs(run_now)

        return run_now
