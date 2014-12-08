#! /usr/bin/env python

import unittest

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

    def testBaseClass(self):
        self.log.info('Testing Command base class')
        command = Command()
        command.execute()

    def testCopyFile(self):
        command = copyfile.CopyFile(remote_host=self.remote_host, source=__file__, destination='/tmp/')

    def testAddDaemontools(self):
        command = adddaemontools.AddDaemontools(remote_host=self.remote_host, servicename='NO SUCH SERVICE')

    def testRemoveDaemontools(self):
        command = removedaemontools.RemoveDaemontools(remote_host=self.remote_host, servicename='NO SUCH SERVICE')

    def testCheckService(self):
        command = checkservice.CheckService(remote_host=self.remote_host, check_command='/bin/true')

    def testCleanUp(self):
        command = cleanup.CleanUp(remote_host=self.remote_host, path='/tmp', filespec='NO_SUCH_FILESPEC', keepversions=99)

    def testCreateDirectory(self):
        command = createdirectory.CreateDirectory(remote_host=self.remote_host, source='/tmp/NO_SUCH_DIRECTORY')

    def testDBMigration(self):
        command = dbmigration.DBMigration(remote_host=self.remote_host, source='/tmp/NO_SUCH_DIRECTORY/NO_SUCH_DIRECTORY')

    def testDeployAndRestart(self):
        command = deployandrestart.DeployAndRestart(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE_1')

        command = deployandrestart.DeployAndRestart(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE_1',
          destination='/tmp/NO_SUCH_FILE_2', stop_command='/bin/true', start_command='/bin/true')

        command = deployandrestart.DeployAndRestart(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE_1',
          destination='/tmp/NO_SUCH_FILE_2', stop_command='/bin/true', start_command='/bin/true',
          lb_hostname='NO_HOSTNAME', lb_username='NO_USERNAME', lb_password='NO_PASSWORD', lb_service='NO_SERVICE',
          check_command='/bin/true', control_timeout=10, lb_timeout=10)

    def testDeployProperties(self):
        command = deployproperties.DeployProperties(remote_host=self.remote_host, source='/tmp/NO_SUCH_DIRECTORY_1',
          destination='/tmp/NO_SUCH_DIRECTORY_2', version=1)

    def testMoveFile(self):
        command = movefile.MoveFile(remote_host=self.remote_host, source='/tmp/NO_SUCH_DIRECTORY', destination='/tmp/NO_SUCH_DIRECTORY')

    def testRemoveFile(self):
        command = removefile.RemoveFile(remote_host=self.remote_host, source='/tmp/NO_SUCH_DIRECTORY')

    def testEnableLoadbalancer(self):
        command = enableloadbalancer.EnableLoadbalancer(lb_hostname='NO_HOSTNAME', lb_username='NO_USERNAME',
          lb_password='NO_PASSWORD', lb_service='NO_SERVICE')
        command = enableloadbalancer.EnableLoadbalancer(lb_hostname='NO_HOSTNAME', lb_username='NO_USERNAME',
          lb_password='NO_PASSWORD', lb_service='NO_SERVICE', timeout=10, continue_on_fail=True)

    def testDisableLoadbalancer(self):
        command = disableloadbalancer.DisableLoadbalancer(lb_hostname='NO_HOSTNAME', lb_username='NO_USERNAME',
          lb_password='NO_PASSWORD', lb_service='NO_SERVICE')
        command = disableloadbalancer.DisableLoadbalancer(lb_hostname='NO_HOSTNAME', lb_username='NO_USERNAME',
          lb_password='NO_PASSWORD', lb_service='NO_SERVICE', timeout=10, continue_on_fail=True)

    def testStartService(self):
        command = startservice.StartService(remote_host=self.remote_host, start_command='/bin/true')
        command = startservice.StartService(remote_host=self.remote_host, start_command='/bin/true',
          check_command='/bin/true', timeout=10)

    def testStopService(self):
        command = stopservice.StopService(remote_host=self.remote_host, stop_command='/bin/true')
        command = stopservice.StopService(remote_host=self.remote_host, stop_command='/bin/true',
          check_command='/bin/true', timeout=10)

    def testRestartService(self):
        command = restartservice.RestartService(remote_host=self.remote_host, stop_command='/bin/true',
          start_command='/bin/true')
        command = restartservice.RestartService(remote_host=self.remote_host, stop_command='/bin/true',
          start_command='/bin/true', lb_hostname='NO_HOSTNAME', lb_username='NO_USERNAME',
          lb_password='NO_PASSWORD', lb_service='NO_SERVICE')

    def testControlService(self):
        command = controlservice.ControlService(remote_host=self.remote_host, control_command='/bin/true')

    def testSendGraphite(self):
        command = sendgraphite.SendGraphite(carbon_host=self.remote_host.hostname, metric_name='mp.test')
        command = sendgraphite.SendGraphite(carbon_host=self.remote_host.hostname, metric_name='mp.test',
          metric_value=10, carbon_port=8888, continue_on_fail=False)

    def testSymLink(self):
        command = symlink.SymLink(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE_1',
          destination='/tmp/NO_SUCH_FILE_2')
        command = symlink.SymLink(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE_1',
          destination='/tmp/NO_SUCH_FILE_2', clobber=False)

    def testUpload(self):
        command = upload.Upload(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE', destination='/tmp/NO_SUCH_DIRECTORY')

    def testUnpack(self):
        command = unpack.Unpack(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE.tar.gz',
          destination='/tmp/NO_SUCH_DIRECTORY')

        with self.assertRaises(DeployerException):
            command = unpack.Unpack(remote_host=self.remote_host, source='/tmp/NO_SUCH_FILE.NO_SUCH_EXTENTION',
              destination='/tmp/NO_SUCH_DIRECTORY')

    def testTestCommand(self):
        command = testcommand.TestCommand(message='Test Message')
        command.execute()


if __name__ == '__main__':
    unittest.main()
