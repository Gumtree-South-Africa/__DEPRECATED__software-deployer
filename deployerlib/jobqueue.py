"""Fabric's job_queue.py with some additions"""

"""
Sliding-window-based job/task queue class (& example of use.)

May use ``multiprocessing.Process`` or ``threading.Thread`` objects as queue
items, though within Fabric itself only ``Process`` objects are used/supported.
"""

import time
import Queue
import signal

from fabric.state import env
from fabric.network import ssh
from fabric.context_managers import settings

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class JobQueue(object):
    """
    The goal of this class is to make a queue of processes to run, and go
    through them running X number at any given time.

    So if the bubble is 5 start with 5 running and move the bubble of running
    procs along the queue looking something like this:

        Start
        ...........................
        [~~~~~]....................
        ___[~~~~~].................
        _________[~~~~~]...........
        __________________[~~~~~]..
        ____________________[~~~~~]
        ___________________________
                                End
    """
    def __init__(self, remote_results, max_running, max_per_host=None, abort_on_error=True):
        """
        Setup the class to resonable defaults.
        """

        self.log = Log(self.__class__.__name__)
        self.remote_results = remote_results
        self.not_run = 'NOTRUN'
        self._queued = []
        self._running = []
        self._completed = []
        self._aborted = []
        self._abort_flag = False
        self._num_of_jobs = 0
        self._max = max_running
        self._max_per_host = max_per_host
        self._comms_queue = Queue.Queue()
        self._finished = False
        self._closed = False
        self.abort_on_error=abort_on_error

    def _all_alive(self):
        """
        Simply states if all procs are alive or not. Needed to determine when
        to stop looping, and pop dead procs off and add live ones.
        """
        if self._running:
            return all([x.is_alive() for x in self._running])
        else:
            return False

    def __len__(self):
        """
        Just going to use number of jobs as the JobQueue length.
        """
        return self._num_of_jobs

    def close(self):
        """
        A sanity check, so that the need to care about new jobs being added in
        the last throws of the job_queue's run are negated.
        """
        self.log.debug("job queue closed.")

        self._closed = True

    def append(self, processlist):
        """
        Add the Process() to the queue, so that later it can be checked up on.
        That is if the JobQueue is still open.

        If the queue is closed, this will just silently do nothing.

        To get data back out of this process, give ``process`` access to a
        ``multiprocessing.Queue`` object, and give it here as ``queue``. Then
        ``JobQueue.run`` will include the queue's contents in its return value.
        """

        if self._closed:
            return

        if not hasattr(processlist, '__iter__'):
            processlist = [processlist]

        for process in processlist:
            self._queued.append(process)
            self._num_of_jobs += 1
            # prime with not_run string to differentiate failed jobs from jobs
            # which have not run
            self.remote_results[process.name] = self.not_run
            self.log.hidebug('{0} appended job {1}'.format(self.__class__.__name__, process.name))

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

            Returns True if a job was started, False if not job was able to be
            started.
            """

            if not self._queued:
                self.log.debug('Job queue is empty')
                return False

            for idx, job_candidate in enumerate(self._queued):

                # Check _max_per_host threshold before starting a job
                if self._max_per_host:
                    if len([x for x in self._running if x._host == job_candidate._host]) >= self._max_per_host:
                        self.log.debug('Skipping job {0}, already {1} jobs running on {2}'.format(
                          job_candidate, self._max_per_host, job_candidate._host))
                        continue

                # Check for job dependencies
                if job_candidate.depends:
                    if not [x for x in self._completed if x._name == job_candidate.depends]:
                        # Make sure the parent job exists
                        if not [x for x in self._running + self._queued if x._name == job_candidate.depends]:
                            self.log.error('Job {0} depends on non-existent job {1}'.format(job_candidate._name, job_candidate.depends))
                            _abort_queue([job_candidate])

                        self.log.hidebug('Job {0} is waiting for job {1} to complete'.format(job_candidate._name, job_candidate.depends))
                        continue

                job = self._queued.pop(idx)
                self.log.debug('Starting job: {0}'.format(job._name))

                with settings(clean_revert=True, host_string=job._host, host=job._host):
                    job.start()

                self._running.append(job)

                return True

            self.log.debug('No jobs available to be started')
            time.sleep(1)

            return False

        def _abort_queue(jobs=[]):
            """Helper function to abort the queue cleanly"""

            self._abort_flag = True

            if jobs:
                self.log.critical('Aborting queue due to failed jobs: {0}'.format(', '.join([x._name for x in jobs])))
                self._aborted += jobs

            # List of jobs that are dependencies of successfully-completed jobs
            allowed_jobs = []
            for job in [x for x in self._completed + self._running if x not in self._aborted]:
                deps = [x for x in _get_dependencies(job) if x in self._queued]

                if deps:
                    self.log.debug('Allowing {0} dependencies to continue for job: {0}'.format(len(deps), job._name))
                    allowed_jobs += deps

            # Abort all other queued jobs
            self._aborted += [x for x in self._queued if x not in allowed_jobs]
            self._queued = [x for x in self._queued if x not in self._aborted]

            if len(self._aborted) > 0:
                self.log.warning('Aborting {0} queued jobs'.format(len(self._aborted)))
                self.log.debug('Aborted jobs: {0}'.format(', '.join([x._name for x in self._aborted])))

            if len(self._running) > 0:
                self.log.warning('Allowing {0} running jobs to finish'.format(len(self._running)))

            self.log.warning('Allowing {0} queued jobs to continue'.format(len(self._queued)))

            return

        def _get_dependencies(job):
            """Helper function to get a list of queued dependencies for a job"""

            deps = [x for x in self._queued + self._running if x.depends == job._name]

            if not deps:
                return deps

            for dep in deps:
                return deps + _get_dependencies(dep)

        def _interrupt_handler(signum, frame):
            """Handle keyboard interrupt"""

            self.log.warning('User interrupt: Aborting the queue cleanly, use Ctrl-C again to abort immediately')
            signal.signal(signal.SIGINT, signal.default_int_handler)
            _abort_queue()

        signal.signal(signal.SIGINT, _interrupt_handler)

        # Prep return value so we can start filling it during main loop
        results = {}
        for job in self._queued:
            results[job.name] = dict.fromkeys(('exit_code', 'results'))

        if not self._closed:
            raise Exception("Need to close() before starting.")

        self.log.debug('Starting job queue')

        while len(self._running) < self._max and len(self._queued) > 0:
            if not _advance_the_queue():
                break

        # Main loop!
        while not self._finished:
            while len(self._running) < self._max and self._queued:
                if not _advance_the_queue():
                    break

            if not self._all_alive():
                # Check for completed jobs and remove them from the _running queue
                completed = [x for x in self._running if not x.is_alive()]

                self._running = [x for x in self._running if not x in completed]
                self._completed += completed

                # Jobs that do not return a result are considered failed
                failed_jobs = [x for x in completed if not self.remote_results[x._name] or self.remote_results[x._name] == self.not_run]

                if failed_jobs:
                    _abort_queue(failed_jobs)

                self.log.debug('{0} jobs running, {1} jobs queued, {2} jobs completed'.format(
                  len(self._running), len(self._queued), len(self._completed)))

            if not (self._queued or self._running):
                if self._abort_flag:
                    self.log.debug('Aborted job queue')
                else:
                    self.log.debug('Finished job queue')

                self._finished = True

            # Each loop pass, try pulling results off the queue to keep its
            # size down. At this point, we don't actually care if any results
            # have arrived yet; they will be picked up after the main loop.
            self._fill_results(results)

            time.sleep(ssh.io_sleep)

        signal.signal(signal.SIGINT, signal.default_int_handler)

        # Consume anything left in the results queue. Note that there is no
        # need to block here, as the main loop ensures that all workers will
        # already have finished.
        self._fill_results(results)

        # Attach exit codes now that we're all done & have joined all jobs
        for job in self._completed:
            results[job.name]['exit_code'] = job.exitcode

        if self._abort_flag and self.abort_on_error:
            return False
        else:
            return True

    def _fill_results(self, results):
        """
        Attempt to pull data off self._comms_queue and add to 'results' dict.
        If no data is available (i.e. the queue is empty), bail immediately.
        """
        while True:
            try:
                datum = self._comms_queue.get_nowait()
                results[datum['name']]['results'] = datum['result']
            except Queue.Empty:
                break
