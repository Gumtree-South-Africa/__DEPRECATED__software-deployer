import os

from Queue import Queue
from multiprocessing import Process
from fabric.job_queue import JobQueue

from deployerlib.log import Log
from deployerlib.service import Service
from deployerlib.deployer import Deployer


class Orchestrator(object):
    """Build deployer objects for each component to be deployed"""

    def __init__(self, config):
        self.config = config
        self.log = Log(self.__class__.__name__)

        self.services = self.get_services()
        self.queue = Queue()
        self.jobs = JobQueue(config.args.parallel, self.queue)

        if config.args.debug:
            self.jobs._debug = True

        self.build_job_queue()

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

        return services

    def build_job_queue(self):
        """Build a list of jobs and add them to the job queue"""

        for service in self.services:
            for host in service.hosts:
                deployer = Deployer(self.config, service, host)
                job = Process(target=deployer.deploy, name=host)
                self.jobs.append(job)

    def run(self):
        """Start running the job queue"""

        self.jobs.close()
        self.jobs.run()
