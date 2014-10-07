import os

from Queue import Queue
from multiprocessing import Process

from deployerlib.log import Log
from deployerlib.service import Service
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

        self.job_list = self.get_job_list()

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

        if self.config.deployment_order:
            services = self.sort_services(services, self.config.deployment_order)
        else:
            self.log.info('No deployment_order has been specified')

        return services

    def sort_services(self, services, order):
        """Sort a list of services according to a specified order
           services: A list of service objects
           order: A list of servicename strings
        """

        newlist = []

        for servicename in order:
            sortitem = next((x for x in services if x.servicename == servicename), None)

            if sortitem:
                newlist.append(sortitem)
            else:
                self.log.debug('Service {0} specified in deployment order, but there is no package to deploy'.format(servicename))

        newlist += [x for x in services if not x in newlist]

        return newlist

    def get_job_list(self):
        """Build a list of jobs"""

        job_list = []

        for service in self.services:
            for host in service.hosts:
                deployer = Deployer(self.config, service, host)
                job = Process(target=deployer.deploy, name=host)
                job._host = host
                job._service = service.servicename
                job_list.append(job)

        return job_list

    def run(self):
        # deploy to a single host
        if hasattr(self.config, 'single_host'):
            single_host = self.config.single_host
        else:
            single_host = self.services[0].hosts[0]

        self._run_host(single_host)

        # run services according to the deployment_order
        if hasattr(self.config, 'deployment_order'):

            for servicename in self.config.deployment_order:
                self._run_service(servicename)

        # run remaining jobs
        self._run_jobs()

    def _run_jobs(self, jobs=None, parallel=None):
        """Start running a job queue"""

        # By default run all jobs in the job list
        if not jobs:
            jobs = self.job_list

        # Abort if the job list is empty
        if not jobs:
            self.log.info('Finished running job queue')
            return

        # By default use the parallel specified on the command line
        if not parallel:
            parallel = self.config.args.parallel

        queue = Queue()
        job_queue = JobQueue(parallel, queue)

        if self.config.args.debug:
            job_queue._debug = True

        # add jobs to queue
        for job in jobs:
            job_queue.append(job)

        # remove queued jobs from the job list
        self.job_list = [x for x in self.job_list if not x in jobs]

        self.log.debug('Running {0} jobs'.format(len(jobs)))

        job_queue.close()
        res = job_queue.run()

        # check results of each job
        failed = [x for x in res.keys() if res[x]['exit_code'] != 0]

        if failed:
            raise DeployerException('Failed jobs: {0}'.format(failed))

        return res

    def _run_host(self, hostname, parallel=1):
        """Run all jobs for the specified hostname"""

        jobs = [x for x in self.job_list if x._host == hostname]

        if not jobs:
            self.log.critical('{0} jobs in the queue, but none are destined for {1}'.format(
              len(self.job_list), hostname))
            raise DeployerException('run_host: No jobs to run for this host')

        self.log.info('Queuing {0} jobs on {1}'.format(len(jobs), hostname))
        self._run_jobs(jobs, parallel)

    def _run_service(self, servicename, parallel=None):
        """Run all jobs for the specified service"""

        if not parallel:
            parallel = self.config.args.parallel

        if not self.job_list:
            self.log.info('Job queue is empty')
            return

        jobs = [x for x in self.job_list if x._service == servicename]

        if not jobs:
            self.log.info('{0} jobs in the queue, but none are for service {1}'.format(
              len(self.job_list), servicename))
            return

        self.log.info('Queuing {0} jobs for service {1}'.format(len(jobs), servicename))
        self._run_jobs(jobs, parallel)
