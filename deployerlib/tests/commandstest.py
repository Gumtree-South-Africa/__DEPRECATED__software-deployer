#! /usr/bin/env python

import unittest

from deployerlib.log import Log
from deployerlib.remotehost import RemoteHost
from deployerlib.command import Command
from deployerlib.exceptions import DeployerException

import deployerlib.commands
from deployerlib.commands import *


class TasklistTest(unittest.TestCase):

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

    def testMoveFile(self):
        command = movefile.MoveFile(remote_host=self.remote_host, source='/tmp/NO_SUCH_DIRECTORY', destination='/tmp/NO_SUCH_DIRECTORY')

    def testRemoveFile(self):
        command = removefile.RemoveFile(remote_host=self.remote_host, source='/tmp/NO_SUCH_DIRECTORY')

    def testTestCommand(self):
        command = testcommand.TestCommand(message='Test Message')
        command.execute()


if __name__ == '__main__':
    unittest.main()
