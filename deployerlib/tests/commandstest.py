#! /usr/bin/env python

import unittest

import deployerlib.commands

from deployerlib.log import Log
from deployerlib.remotehost import RemoteHost
from deployerlib.command import Command
from deployerlib.exceptions import DeployerException

import deployerlib.commands
from deployerlib.commands import *


class CommandsTest(unittest.TestCase):

    def setUp(self):
        self.log = Log(self.__class__.__name__)
        self.remote_host = RemoteHost('localhost')

    def verifyCommand(self, command):
        """Tests that apply to all command objects"""

        # make sure the command is inheriting the Command class
        self.assertIsInstance(command, Command)

    def testAllAreTested(self):
        self.log.info('Making sure there is a test for every command')

        prefix = 'testCommand_'
        methods = [x[len(prefix):] for x in dir(self) if x.startswith(prefix)]

        missing = set(deployerlib.commands.__all__) - set(methods)

        if missing:
            self.fail('Missing command tests: {0}'.format(', '.join(missing)))

    def testCommand(self):
        self.log.info('Testing Command parent class')
        command = Command()
        command.execute()

    def testCommand_testcommand(self):
        command = testcommand.TestCommand(message='Test Message')
        self.verifyCommand(command)
        command.execute()

    def testCommand_copyfile(self):
        command = copyfile.CopyFile(remote_host=self.remote_host, source=__file__, destination='/tmp/')
        self.verifyCommand(command)

    def testCommand_adddaemontools(self):
        command = adddaemontools.AddDaemontools(remote_host=self.remote_host, servicename='NO SUCH SERVICE')
        self.verifyCommand(command)

    def testCommand_removedaemontools(self):
        command = removedaemontools.RemoveDaemontools(remote_host=self.remote_host, servicename='NO SUCH SERVICE')
        self.verifyCommand(command)

    def testCommand_checkservice(self):
        command = checkservice.CheckService(remote_host=self.remote_host, check_command='/bin/true')
        self.verifyCommand(command)

    def testCommand_cleanup(self):
        command = cleanup.CleanUp(remote_host=self.remote_host, path='/tmp', filespec='NO_SUCH_FILESPEC', keepversions=99)
        self.verifyCommand(command)

    def testCommand_createdirectory(self):
        command = createdirectory.CreateDirectory(remote_host=self.remote_host, source='/tmp/NO_SUCH_DIRECTORY')
        self.verifyCommand(command)

    def testCommand_migrationscript(self):
        command = migrationscript.migrationscript(remote_host=self.remote_host, source='/tmp/NO_SUCH_DIRECTORY/NO_SUCH_DIRECTORY')
        self.verifyCommand(command)

    def testCommand_deployandrestart(self):
        command = deployandrestart.DeployAndRestart(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE_1')
        self.verifyCommand(command)

        command = deployandrestart.DeployAndRestart(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE_1',
          destination='/tmp/NO_SUCH_FILE_2', stop_command='/bin/true', start_command='/bin/true')

        command = deployandrestart.DeployAndRestart(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE_1',
          destination='/tmp/NO_SUCH_FILE_2', stop_command='/bin/true', start_command='/bin/true',
          lb_hostname='NO_HOSTNAME', lb_username='NO_USERNAME', lb_password='NO_PASSWORD', lb_service='NO_SERVICE',
          check_command='/bin/true', control_timeout=10, lb_timeout=10)

        self.verifyCommand(command)

    def testCommand_deployproperties(self):
        command = deployproperties.DeployProperties(remote_host=self.remote_host, source='/tmp/NO_SUCH_DIRECTORY_1',
          destination='/tmp/NO_SUCH_DIRECTORY_2', version=1)
        self.verifyCommand(command)

    def testCommand_movefile(self):
        command = movefile.MoveFile(remote_host=self.remote_host, source='/tmp/NO_SUCH_DIRECTORY', destination='/tmp/NO_SUCH_DIRECTORY')
        self.verifyCommand(command)

    def testCommand_removefile(self):
        command = removefile.RemoveFile(remote_host=self.remote_host, source='/tmp/NO_SUCH_DIRECTORY')
        self.verifyCommand(command)

    def testCommand_enableloadbalancer(self):
        command = enableloadbalancer.EnableLoadbalancer(lb_hostname='NO_HOSTNAME', lb_username='NO_USERNAME',
          lb_password='NO_PASSWORD', lb_service='NO_SERVICE')

        command = enableloadbalancer.EnableLoadbalancer(lb_hostname='NO_HOSTNAME', lb_username='NO_USERNAME',
          lb_password='NO_PASSWORD', lb_service='NO_SERVICE', timeout=10, continue_on_fail=True)

        self.verifyCommand(command)

    def testCommand_disableloadbalancer(self):
        command = disableloadbalancer.DisableLoadbalancer(lb_hostname='NO_HOSTNAME', lb_username='NO_USERNAME',
          lb_password='NO_PASSWORD', lb_service='NO_SERVICE')

        command = disableloadbalancer.DisableLoadbalancer(lb_hostname='NO_HOSTNAME', lb_username='NO_USERNAME',
          lb_password='NO_PASSWORD', lb_service='NO_SERVICE', timeout=10, continue_on_fail=True)

        self.verifyCommand(command)

    def testCommand_startservice(self):
        command = startservice.StartService(remote_host=self.remote_host, start_command='/bin/true')

        command = startservice.StartService(remote_host=self.remote_host, start_command='/bin/true',
          check_command='/bin/true', timeout=10)

        self.verifyCommand(command)

    def testCommand_stopservice(self):
        command = stopservice.StopService(remote_host=self.remote_host, stop_command='/bin/true')

        command = stopservice.StopService(remote_host=self.remote_host, stop_command='/bin/true',
          check_command='/bin/true', timeout=10)

        self.verifyCommand(command)

    def testCommand_restartservice(self):
        command = restartservice.RestartService(remote_host=self.remote_host, stop_command='/bin/true',
          start_command='/bin/true')

        command = restartservice.RestartService(remote_host=self.remote_host, stop_command='/bin/true',
          start_command='/bin/true', lb_hostname='NO_HOSTNAME', lb_username='NO_USERNAME',
          lb_password='NO_PASSWORD', lb_service='NO_SERVICE')

        self.verifyCommand(command)

    def testCommand_controlservice(self):
        command = controlservice.ControlService(remote_host=self.remote_host, control_command='/bin/true')
        self.verifyCommand(command)

    def testCommand_sendgraphite(self):
        command = sendgraphite.SendGraphite(carbon_host=self.remote_host.hostname, metric_name='mp.test')

        command = sendgraphite.SendGraphite(carbon_host=self.remote_host.hostname, metric_name='mp.test',
          metric_value=10, carbon_port=8888, continue_on_fail=False)

        self.verifyCommand(command)

    def testCommand_symlink(self):
        command = symlink.SymLink(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE_1',
          destination='/tmp/NO_SUCH_FILE_2')

        self.verifyCommand(command)

    def testCommand_upload(self):
        command = upload.Upload(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE', destination='/tmp/NO_SUCH_DIRECTORY')
        self.verifyCommand(command)

    def testCommand_unpack(self):
        command = unpack.Unpack(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE.tar.gz',
          destination='/tmp/NO_SUCH_DIRECTORY')

        self.verifyCommand(command)

        with self.assertRaises(DeployerException):
            command = unpack.Unpack(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE.NO_SUCH_EXTENTION',
              destination='/tmp/NO_SUCH_DIRECTORY')

    def testCommand_executecommand(self):
        command = executecommand.ExecuteCommand(remote_host=self.remote_host, command='/tmp/NO_SUCH_COMMAND')
        self.verifyCommand(command)

    def testCommand_pipeline_upload(self):
        command = pipeline_upload.PipelineUpload(deploy_package_basedir='/tmp/NO_SUCH_DIRECTORY',
          release='release1', url='http://localhost/')

        command = pipeline_upload.PipelineUpload(deploy_package_basedir='/tmp/NO_SUCH_DIRECTORY',
          release='release1', url='http://localhost/', proxy='localhost:3128', continue_on_fail=False)

        self.verifyCommand(command)

    def testCommand_pipeline_notify(self):
        command = pipeline_notify.PipelineNotify(url='http://localhost/')
        command = pipeline_notify.PipelineNotify(url='http://localhost/', proxy='localhost:3128', continue_on_fail=False)
        self.verifyCommand(command)

    def testCommand_checkdaemontools(self):
        command = checkdaemontools.CheckDaemontools(remote_host=self.remote_host, servicename='testservice')

        command = checkdaemontools.CheckDaemontools(remote_host=self.remote_host, servicename='testservice',
          path='/tmp/NO_SUCH_DIRECTORY')

        self.verifyCommand(command)


if __name__ == '__main__':
    unittest.main()
