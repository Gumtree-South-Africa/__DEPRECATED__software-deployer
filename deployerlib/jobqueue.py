import time

from fabric.job_queue import JobQueue as FabricJobQueue
from fabric.network import ssh
from fabric.context_managers import settings

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class JobQueue(FabricJobQueue):

    def __init__(self, parallel, queue, remote_results={}, *args, **kwargs):
        self.log = Log(self.__class__.__name__)
        self.remote_results = remote_results
        super(self.__class__, self).__init__(parallel, queue, *args, **kwargs)

    def run(self):
        """
        This is the workhorse. It will take the intial jobs from the _queue,
        start them, add them to _running, and then go into the main running
        loop.

        This loop will check for done procs, if found, move them out of
        _running into _completed. It also checks for a _running queue with open
        spots, which it will then fill as discovered.

        To end the loop, there have to be no running procs, and no more procs
        to be run in the queue.

        This function returns an iterable of all its children's exit codes.
        """
        def _advance_the_queue():
            """
            Helper function to do the job of poping a new proc off the queue
            start it, then add it to the running queue. This will eventually
            depleate the _queue, which is a condition of stopping the running
            while loop.

            It also sets the env.host_string from the job.name, so that fabric
            knows that this is the host to be making connections on.
            """
            job = self._queued.pop(0)
            self.log.debug('Starting job: {0}'.format(job._name))

            with settings(clean_revert=True, host_string=job._host, host=job._host):
                job.start()

            self._running.append(job)

        def _abort_queue(jobs):

            msg = 'Aborting queue due to failed jobs'

            if jobs:

                if type(jobs) is list:
                    msg += ': {0}'.format(', '.join(jobs))
                else:
                    msg += ': {0}'.format(jobs)

            self.log.critical(msg)

            if len(self._running) > 1:
                self.log.warning('Allowing {0} jobs to finish'.format(len(self._running) - 1))

            for job in self._completed:
                job.join()

            self._fill_results(results)
            time.sleep(ssh.io_sleep)

            return results

        # Prep return value so we can start filling it during main loop
        results = {}
        for job in self._queued:
            results[job.name] = dict.fromkeys(('exit_code', 'results'))

        if not self._closed:
            raise Exception("Need to close() before starting.")

        self.log.debug('Starting job queue')

        while len(self._running) < self._max and len(self._running) > 0:
            _advance_the_queue()

        # Main loop!
        while not self._finished:
            while len(self._running) < self._max and self._queued:
                _advance_the_queue()

            if not self._all_alive():
                for id, job in enumerate(self._running):
                    if not job.is_alive():
                        self.log.debug('Found finished job: {0}'.format(job._name))

                        if not job._name in self.remote_results:
                            # populate this so the orchestrator will know a job failed
                            self.remote_results[job._name] = False

                        if not self.remote_results[job._name]:
                            _abort_queue(job._name)
                        done = self._running.pop(id)
                        self._completed.append(done)

                self.log.debug('{0} jobs running and {1} jobs queued'.format(
                  len(self._running), len(self._queued)))

            if not (self._queued or self._running):
                self.log.debug('Finished job queue')

                for job in self._completed:
                    job.join()

                self._finished = True

            # Each loop pass, try pulling results off the queue to keep its
            # size down. At this point, we don't actually care if any results
            # have arrived yet; they will be picked up after the main loop.
            self._fill_results(results)

            time.sleep(ssh.io_sleep)

        # Consume anything left in the results queue. Note that there is no
        # need to block here, as the main loop ensures that all workers will
        # already have finished.
        self._fill_results(results)

        # Attach exit codes now that we're all done & have joined all jobs
        for job in self._completed:
            results[job.name]['exit_code'] = job.exitcode

        return results
