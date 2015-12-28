import os
import json
import time
import signal

from fabric.colors import green
from fabric.network import disconnect_all
from multiprocessing import Process
from multiprocessing.managers import SyncManager

from deployerlib.commands import *

from deployerlib.log import Log
from deployerlib.remotehost import RemoteHost
from deployerlib.jobqueue import JobQueue
from deployerlib.exceptions import DeployerException


class Executor(object):
    """Build deployer objects for each component to be deployed"""

    def __init__(self, filename=None, tasklist=None):
        self.log = Log(self.__class__.__name__)

        # translate external command names into class names
        self.callables = {
          'upload': upload.Upload,
          'unpack': unpack.Unpack,
          'migration_script': migrationscript.MigrationScript,
          'createdirectory': createdirectory.CreateDirectory,
          'copyfile': copyfile.CopyFile,
          'movefile': movefile.MoveFile,
          'writefile': writefile.WriteFile,
          'removefile': removefile.RemoveFile,
          'deploy_and_restart': deployandrestart.DeployAndRestart,
          'deploy_properties': deployproperties.DeployProperties,
          'control_service': controlservice.ControlService,
          'stop_service': stopservice.StopService,
          'start_service': startservice.StartService,
          'restart_service': restartservice.RestartService,
          'reload_service': reloadservice.ReloadService,
          'check_service': checkservice.CheckService,
          'symlink': symlink.SymLink,
          'disable_loadbalancer': disableloadbalancer.DisableLoadbalancer,
          'enable_loadbalancer': enableloadbalancer.EnableLoadbalancer,
          'execute_command': executecommand.ExecuteCommand,
          'send_graphite': sendgraphite.SendGraphite,
          'pipeline_notify': pipeline_notify.PipelineNotify,
          'pipeline_upload': pipeline_upload.PipelineUpload,
          'cleanup': cleanup.CleanUp,
          'archive': archive.Archive,
          'test_command': testcommand.TestCommand,
          'listdirectory': listdirectory.ListDirectory,
          'getremoteversions': getremoteversions.GetRemoteVersions,
          'daemontools': daemontools.DaemonTools,
          'apache': apache.Apache,
          'createdeploypackage': createdeploypackage.CreateDeployPackage,
          'deploymonitor_notify': deploymonitor_notify.DeploymonitorNotify,
          'deploymonitor_createpackage': deploymonitor_createpackage.DeploymonitorCreatePackage,
          'deploymonitor_upload': deploymonitor_upload.DeploymonitorUpload,
          'local_cleanup': localcleanup.LocalCleanUp,
          'local_createdirectory': localcreatedirectory.LocalCreateDirectory,
          'consul_service': consulservice.ConsulService,
        }

        # Start manager manually in order to have the child processes ignore
        # SIGINT, allowing KeyboardInterrupt to be handled by the parent
        manager = SyncManager()
        manager.start(lambda *args: signal.signal(signal.SIGINT, signal.SIG_IGN))

        self.remote_hosts = []
        self.remote_results = manager.dict()

        if not tasklist:

            if not filename:
                raise DeployerException('Empty tasklist and no filename specified')

            tasklist = self.read_tasklist(filename)

        self.stages = self.parse_stages(tasklist)
        self.log.info('Tasklist loaded successfully')

    def read_tasklist(self, filename):
        """Read in a task list and generate a list of jobs"""

        j = None
        self.log.info('Reading task list from {0}'.format(filename))

        with open(filename, 'r') as f:

            try:
                j = json.load(f)
            except ValueError as e:
                raise DeployerException('Error parsing task list {0} as json: {1}'.format(
                    filename, e))

        if not j:
            raise DeployerException('No task list found in file {0}'.format(filename))

        return j

    def parse_stages(self, tasklist):
        """Parse each stage and create a list of runnable jobs
           A stage is a dictionary in the form:
           {
               'name': '<Arbitrary name for this stage>',
               'concurrency': '<Number of jobs to run in parallel>',
               'concurrency_per_host': '<Maximum number of jobs per host to run in parallel>',
               'tasks': [<list of task dicts>]
           }
        """

        stages = []

        for i in tasklist['stages']:
            ext_stage = i.copy()
            stage = {}

            for required_key in ['name', 'concurrency', 'tasks']:

                try:
                    stage[required_key] = ext_stage.pop(required_key)
                except KeyError as e:

                    if 'name' in stage:
                        msg = 'Stage {0} missing required key: {1}'.format(stage['name'], e)
                    else:
                        msg = 'Found stage with no name: {0}'.format(ext_stage)

            for optional_key in ['concurrency_per_host']:

                try:
                    stage[optional_key] = ext_stage.pop(optional_key)
                except KeyError:
                    stage[optional_key] = None

            if ext_stage:
                raise DeployerException('Unknown key found in stage {0}: {1}'.format(
                  stage['name'], ', '.join(ext_stage.keys())))

            self.log.debug('Parsing stage {0}'.format(stage['name']))

            stage['tasks'] = self.parse_tasks(stage['tasks'])
            stages.append(stage)

            self.log.debug('Added {0} jobs for stage {1}'.format(len(stage['tasks']), stage['name']))

        self.log.debug('Parsed {0} stages'.format(len(stages)))

        return stages

    def parse_tasks(self, tasks):
        """Build executable jobs from a list of tasks
           A task is a dictionary in the form:
           {
               'command':     '<pre-defined internal command>'
               'remote_host': '<remote host on which to run the command>',
               'remote_user': '<username as which to log in to the remote host>',
               'arg1':        '<argument to internal command>',
               ...
           }
           'command' is required, and must be defined in the Orchestrator
           'remote_host' is optional, and will be replaced by a RemoteHost object
           'remote_user' is optional, and will be passed to the RemoteHost object (and not to the internal command)
        """
        def queue_task(_task, parent_task=None):
            """Create a job and add it to the job queue"""

            task = _task.copy()

            if not 'command' in task:
                raise DeployerException('No command specified in task: {0}'.format(task))

            if not task['command'] in self.callables:
                raise DeployerException('Command "{0}" is not implemented'.format(task['command']))

            callable = self.callables[task.pop('command')]

            if 'remote_host' in task:

                if 'remote_user' in task:
                    username = task.pop('remote_user')
                else:
                    username = None

                task['remote_host'] = self.get_remote_host(task['remote_host'], username)
                job_id = task['remote_host'].hostname
            elif 'lb_hostname' in task:
                job_id = task['lb_hostname']
            else:
                job_id = 'local'

            try:
                remote_task = callable(**task)
            except TypeError as e:
                raise DeployerException('Error initializing {0}: {1}'.format(
                  callable.__name__, e))

            procname = repr(remote_task)

            job = Process(target=remote_task.thread_execute, name=procname, args=[procname, self.remote_results])
            job._host = job_id
            job.depends = parent_task

            job_list.append(job)

            return procname

        job_list = []

        for _task in tasks:
            # Handle a list of tasks that must be executed in order
            if type(_task) == list:
                parent_task = None

                for item in _task:
                    parent_task = queue_task(item, parent_task)

            # Handle a single task
            else:
                queue_task(_task)

        return job_list

    def get_remote_host(self, hostname, username=''):
        """Return a host object from a hostname"""

        match = [x for x in self.remote_hosts if x.hostname == hostname]

        if len(match) == 1:
            return match[0]
        elif len(match) > 1:
            raise DeployerException('More than one host found with hostname{0}'.format(hostname))
        else:
            host = RemoteHost(hostname, username)
            self.remote_hosts.append(host)
            return host

    def run(self):
        """Run each stage"""

        self.log.debug('Discarding unused remote connections')
        disconnect_all()

        tasklist_start_time = time.time()

        for idx, stage in enumerate(self.stages):

            self.remote_results.clear()

            if not stage['tasks']:
                self.log.info('No tasks for stage: {0}'.format(stage['name']))

            start_time = time.time()
            self.log.info(green('Starting stage: {0}'.format(stage['name'])))

            job_queue = JobQueue(self.remote_results, stage['concurrency'], stage['concurrency_per_host'])

            for task in stage['tasks']:
                job_queue.append(task)

            job_queue.close()
            queue_success = job_queue.run()

            duration = int(time.time() - start_time)
            failed = [x for x in self.remote_results.keys() if not self.remote_results[x]]

            if failed or not queue_success:
                self.log.error('Failed stage: {0}'.format(stage['name']))

                for failed_job in failed:
                    self.log.error('Failed job: {0}'.format(failed_job))

                for not_run in [x for x in self.remote_results.keys() if self.remote_results[x] == job_queue.not_run]:
                    self.log.debug('Job not run due to aborted queue: {0}'.format(not_run))

                raise DeployerException('Failed jobs')

            else:
                self.log.info(green('Finished stage: {0}'.format(stage['name'])))

            self.log.verbose('Stage {0} execution duration: {1} seconds ({2})'.format(
              idx, duration, stage['name']))

        tasklist_duration = int(time.time() - tasklist_start_time)
        self.log.verbose('GeneratorHelper execution duration: {0} seconds'.format(tasklist_duration))

        return True
