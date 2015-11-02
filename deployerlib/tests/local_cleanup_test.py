#! /usr/bin/env python

import unittest
import mock
import string

from deployerlib.commands import *

class LocalCleanUpTest(unittest.TestCase):

    @mock.patch('deployerlib.commands.localcleanup.subprocess.Popen')
    @mock.patch('deployerlib.commands.localcleanup.shutil')
    @mock.patch('deployerlib.commands.localcleanup.os')
    def test_cleans_up_subdirs_keeping_last_five(self, mock_os, mock_shutil, mock_subproc_popen):
        directory_contents = ['aurora-aurora-core-20151030190949',
                              'aurora-aurora-core-20151030192920',
                              'aurora-aurora-core-20151031011256',
                              'aurora-aurora-core-20151101021323',
                              'aurora-user-services-20151020020255',
                              'aurora-user-services-20151021010311']

        process_mock = mock.Mock()
        attrs = {'communicate.return_value': ('%s' % string.join(directory_contents,"\n"), 'error')}
        process_mock.configure_mock(**attrs)
        mock_subproc_popen.return_value = process_mock

        mock_os.path.isdir.return_value = True

        dir_name = "/bogus"
        package_to_remove = 'aurora-user-services-20151021010311'
        mock_os.path.join.return_value = "%s/%s" % (dir_name, package_to_remove)
        mock_shutil.rmtree.return_value = 1

        cleanup = localcleanup.LocalCleanUp(path=dir_name,filespec="*",keepversions=5)

        cleanup.execute()

        self.assertTrue(mock_subproc_popen.called)
        mock_shutil.rmtree.assert_called_with('/bogus/aurora-user-services-20151021010311')

if __name__ == '__main__':
    unittest.main()
